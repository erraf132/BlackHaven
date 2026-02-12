"""Core framework logic for BlackHaven Framework."""

from __future__ import annotations

import importlib
import json
import os
import pkgutil
import shlex
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List

from core.utils import ConfigManager, JSONStore, Output, Timer, setup_logger


BANNER = r"""
██████╗ ██╗      █████╗  ██████╗██╗  ██╗██╗  ██╗ █████╗ ██╗   ██╗███████╗███╗   ██╗
██╔══██╗██║     ██╔══██╗██╔════╝██║ ██╔╝██║  ██║██╔══██╗██║   ██║██╔════╝████╗  ██║
██████╔╝██║     ███████║██║     █████╔╝ ███████║███████║██║   ██║█████╗  ██╔██╗ ██║
██╔══██╗██║     ██╔══██║██║     ██╔═██╗ ██╔══██║██╔══██║╚██╗ ██╔╝██╔══╝  ██║╚██╗██║
██████╔╝███████╗██║  ██║╚██████╗██║  ██╗██║  ██║██║  ██║ ╚████╔╝ ███████╗██║ ╚████║
╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚══════╝╚═╝  ╚═══╝
"""


@dataclass
class ModuleResult:
    """Structured result record for each module execution."""

    name: str
    target: str
    success: bool
    data: Dict[str, Any]
    elapsed: float


class BlackHavenFramework:
    """Main interactive framework shell."""

    def __init__(self) -> None:
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.modules: Dict[str, Callable[..., Dict[str, Any]]] = {}
        self.last_results: Dict[str, Any] = {"runs": []}
        self.session_id = time.strftime("%Y%m%d-%H%M%S")
        self.config = ConfigManager(os.path.join(self.base_dir, "config.yaml"))

        output_dir = self.config.get("output_directory", os.path.join(self.base_dir, "output"))
        if not os.path.isabs(output_dir):
            output_dir = os.path.join(self.base_dir, output_dir)
        self.output_dir = output_dir
        self.sessions_dir = os.path.join(self.base_dir, "sessions")
        self.logs_dir = os.path.join(self.base_dir, "logs")
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.sessions_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

        self.log_path = os.path.join(self.logs_dir, "blackhaven.log")
        self.logger = setup_logger(self.log_path)
        self._load_modules()

    def _load_modules(self) -> None:
        """Discover and load modules from the modules package."""

        base_path = os.path.join(os.path.dirname(__file__), "..", "modules")
        base_package = "modules"

        for _, module_name, _ in pkgutil.iter_modules([base_path]):
            try:
                module = importlib.import_module(f"{base_package}.{module_name}")
                if hasattr(module, "register"):
                    module.register(self)
                    self.logger.info("Loaded module: %s", module_name)
            except Exception as exc:
                self.logger.error("Failed to load module %s: %s", module_name, exc)

    def register_module(self, name: str, handler: Callable[..., Dict[str, Any]]) -> None:
        """Register a module handler callable."""

        self.modules[name] = handler

    def run(self) -> None:
        """Run the interactive shell."""

        Output.success("BlackHaven Framework initialized (ethical recon only).")
        Output.header(BANNER)
        Output.info("Type 'help' for available commands.")

        while True:
            try:
                raw = input("blackhaven> ")
            except (EOFError, KeyboardInterrupt):
                print()
                break

            command = raw.strip()
            if not command:
                continue

            if command in {"exit", "quit"}:
                break

            if command == "help":
                self._print_help()
                continue

            self._dispatch(command)

        Output.info("Session ended.")

    def _print_help(self) -> None:
        """Display help information."""

        lines = [
            "help",
            "scan domain <target>",
            "scan ports <target>",
            "scan subdomains <target>",
            "scan tech <target>",
            "osint username <handle>",
            "modules list",
            "modules run <module> <target>",
            "config show",
            "session save",
            "session load <filename>",
            "session list",
            "report html",
            "save <path>",
            "exit",
        ]
        Output.info("Available commands:")
        for line in lines:
            print(f"  - {line}")

    def _dispatch(self, command: str) -> None:
        """Parse and route a command to the correct module."""

        try:
            parts = shlex.split(command)
        except ValueError as exc:
            Output.error(f"Command parse error: {exc}")
            return

        if not parts:
            return

        if parts[0] == "save" and len(parts) == 2:
            self._save_results(parts[1])
            return

        if parts[0] == "modules" and len(parts) >= 2:
            self._handle_modules(parts)
            return

        if parts[0] == "config" and len(parts) == 2 and parts[1] == "show":
            self._show_config()
            return

        if parts[0] == "session" and len(parts) >= 2:
            self._handle_session(parts)
            return

        if parts[0] == "report" and len(parts) == 2 and parts[1] == "html":
            self._export_html_report()
            return

        if parts[0] == "scan" and len(parts) >= 3:
            self._handle_scan(parts)
            return

        if parts[0] == "osint" and len(parts) >= 3:
            self._handle_osint(parts)
            return

        Output.warning("Unknown command. Type 'help' for usage.")

    def _handle_modules(self, parts: List[str]) -> None:
        """List modules or run a module directly."""

        if parts[1] == "list":
            Output.info("Loaded modules:")
            for module_name in sorted(self.modules.keys()):
                print(f"  - {module_name}")
            return

        if parts[1] == "run" and len(parts) >= 4:
            module_name = parts[2]
            target = parts[3]
            self._run_module(module_name, target)
            return

        Output.warning("Usage: modules list | modules run <module> <target>")

    def _handle_scan(self, parts: List[str]) -> None:
        """Handle scan commands."""

        scan_type = parts[1]
        target = parts[2]
        mapping = {
            "domain": "domain_recon",
            "ports": "port_scanner",
            "subdomains": "subdomain_enum",
            "tech": "tech_detection",
        }
        module_name = mapping.get(scan_type)
        if not module_name:
            Output.warning("Unsupported scan type.")
            return

        self._run_module(module_name, target)

    def _handle_osint(self, parts: List[str]) -> None:
        """Handle OSINT commands."""

        if parts[1] != "username":
            Output.warning("Supported OSINT target: username")
            return
        target = parts[2]
        self._run_module("osint_lookup", target)

    def _run_module(self, module_name: str, target: str) -> None:
        """Execute a module handler with timing and logging."""

        handler = self.modules.get(module_name)
        if not handler:
            Output.error(f"Module not found: {module_name}")
            return

        Output.info(f"Running {module_name} on {target}...")
        self.logger.info("Running %s on %s", module_name, target)
        with Timer() as timer:
            try:
                data = handler(target, self.config)
                success = True
            except Exception as exc:
                self.logger.exception("Module %s failed: %s", module_name, exc)
                Output.error(f"{module_name} failed: {exc}")
                data = {"error": str(exc)}
                success = False

        result = ModuleResult(
            name=module_name,
            target=target,
            success=success,
            data=data,
            elapsed=timer.elapsed,
        )
        self.logger.info("Completed %s in %.4fs", module_name, result.elapsed)
        self._record_result(result)
        self._auto_save_session()

    def _record_result(self, result: ModuleResult) -> None:
        """Persist result to in-memory session store."""

        record = {
            "module": result.name,
            "target": result.target,
            "success": result.success,
            "elapsed_seconds": round(result.elapsed, 4),
            "data": result.data,
        }

        self._attach_risk_score(record)
        self.last_results["runs"].append(record)
        status = "completed" if result.success else "failed"
        Output.success(f"{result.name} {status} in {record['elapsed_seconds']}s")

    def _save_results(self, path: str) -> None:
        """Save results to a JSON file."""

        try:
            JSONStore.write(path, self.last_results)
            Output.success(f"Results saved to {path}")
        except Exception as exc:
            Output.error(f"Failed to save results: {exc}")

    def _attach_risk_score(self, record: Dict[str, Any]) -> None:
        """Compute a simple risk score based on available scan data."""

        score = 0
        data = record.get("data", {})

        if record["module"] == "port_scanner":
            open_ports = data.get("open_ports", [])
            score += min(len(open_ports) * 2, 40)
            exposed = data.get("exposed_services", [])
            score += min(len(exposed) * 3, 30)

        if record["module"] == "tech_detection":
            technologies = data.get("detected_technologies", [])
            score += min(len(technologies) * 5, 30)

        if score >= 60:
            risk = "High"
        elif score >= 30:
            risk = "Medium"
        else:
            risk = "Low"

        record["risk_score"] = {"score": score, "level": risk}

    def _auto_save_session(self) -> None:
        """Persist the current session data with a timestamped filename."""

        filename = f"session-{self.session_id}.json"
        path = os.path.join(self.sessions_dir, filename)
        try:
            JSONStore.write(path, self.last_results)
            self._auto_save_output()
        except Exception as exc:
            self.logger.error("Failed to auto-save session: %s", exc)

    def _auto_save_output(self) -> None:
        """Persist a timestamped JSON report to the output directory."""

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"blackhaven-results-{timestamp}.json"
        path = os.path.join(self.output_dir, filename)
        try:
            JSONStore.write(path, self.last_results)
        except Exception as exc:
            self.logger.error("Failed to auto-save output: %s", exc)

    def _handle_session(self, parts: List[str]) -> None:
        """Handle session management commands."""

        if parts[1] == "save":
            self._auto_save_session()
            Output.success("Session saved.")
            return

        if parts[1] == "list":
            sessions = sorted(os.listdir(self.sessions_dir))
            Output.info("Available sessions:")
            for name in sessions:
                print(f"  - {name}")
            return

        if parts[1] == "load" and len(parts) == 3:
            filename = parts[2]
            path = os.path.join(self.sessions_dir, filename)
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    self.last_results = json.load(handle)
                Output.success(f"Session loaded from {filename}")
            except Exception as exc:
                Output.error(f"Failed to load session: {exc}")
            return

        Output.warning("Usage: session save | session load <filename> | session list")

    def _show_config(self) -> None:
        """Print current configuration values."""

        Output.info("Current configuration:")
        for key, value in self.config.data.items():
            print(f"  - {key}: {value}")

    def _export_html_report(self) -> None:
        """Export the latest results to an HTML report."""

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"blackhaven-report-{timestamp}.html"
        path = os.path.join(self.output_dir, filename)

        html = [
            "<html>",
            "<head>",
            "<meta charset='utf-8'/>",
            "<title>BlackHaven Report</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; background: #0b0f16; color: #e6e6e6; }",
            "h1, h2 { color: #5cc8ff; }",
            "pre { background: #111827; padding: 12px; border-radius: 6px; overflow-x: auto; }",
            "</style>",
            "</head>",
            "<body>",
            "<h1>BlackHaven Framework Report</h1>",
            f"<p>Generated: {timestamp}</p>",
        ]

        for run in self.last_results.get("runs", []):
            html.append(f"<h2>{run['module']} - {run['target']}</h2>")
            html.append(f"<p>Status: {'Success' if run['success'] else 'Failed'}</p>")
            html.append(f"<p>Elapsed: {run['elapsed_seconds']}s</p>")
            html.append("<pre>")
            html.append(json.dumps(run["data"], indent=2, sort_keys=True))
            html.append("</pre>")

        html.extend(["</body>", "</html>"])

        try:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("\n".join(html))
            Output.success(f"HTML report saved to {path}")
        except Exception as exc:
            Output.error(f"Failed to export HTML report: {exc}")
