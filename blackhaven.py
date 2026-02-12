"""
BlackHaven Framework
Copyright (c) 2026 erraf132 and Vyrn.exe Official
All rights reserved.
"""



import argparse
import sys
import time
from typing import Callable
import types

import updater
from colorama import Fore, Style, init

from framework.core.framework import Framework


VERSION = "1.0.0"

init(autoreset=True)

LEGAL_NOTICE = """============================================================
BLACKHAVEN FRAMEWORK — LEGAL NOTICE
===================================

This software is intended for educational purposes and authorized security research only.

Unauthorized use of this software against systems without explicit permission is illegal.

The author is not responsible for any misuse, damage, or illegal activities conducted with this software.

By using BlackHaven, you agree that you are solely responsible for your actions.

Copyright (c) 2026 erraf132. All rights reserved.

Type "I AGREE" to continue or Ctrl+C to exit.

============================================================
"""


def require_legal_acknowledgement() -> None:
    print(LEGAL_NOTICE)
    while True:
        response = input("> ").strip()
        if response == "I AGREE":
            return
        print('Confirmation not received. Type "I AGREE" to continue or Ctrl+C to exit.')


class BlackHavenArgumentParser(argparse.ArgumentParser):
    """Argument parser with consistent error handling."""

    def format_help(self) -> str:
        options = [
            "  -h, --help                 Show this help message",
            "  -o, --output FILE          Save output to file",
            "  -v, --verbose              Enable verbose output",
            "  -t, --threads INT           Number of threads",
            "  --generate-completion      Generate bash auto-completion script",
            "  --version                  Show version",
        ]

        commands = [
            "  scan        Run reconnaissance modules",
            "  osint       Run OSINT modules",
            "  modules     Manage modules",
            "  session     Manage sessions",
            "  report      Export reports",
            "  config      Show configuration",
        ]

        examples = [
            "  blackhaven scan domain example.com",
            "  blackhaven scan ports example.com",
            "  blackhaven osint username johndoe",
            "  blackhaven report html",
        ]

        lines = [
            f"BlackHaven Framework v{VERSION}",
            "Modular Cybersecurity Recon Framework",
            "",
            "Usage:",
            "  blackhaven <command> [options]",
            "",
            "Commands:",
            *commands,
            "",
            "Options:",
            *options,
            "",
            "Examples:",
            *examples,
            "",
        ]
        return "\n".join(lines)

    def error(self, message: str) -> None:
        if "the following arguments are required:" in message:
            required = message.split(":", 1)[1].strip()
            if required == "scan_type":
                required = "target"
            if required == "osint_type":
                required = "username"
            if required == "modules_cmd":
                required = "module"
            if required == "session_cmd":
                required = "name"
            if required == "report_type":
                required = "format"
            if required == "config_cmd":
                required = "command"
            if "," in required:
                message = f"missing required arguments: {required}"
            else:
                message = f"missing required argument: {required}"
        self.print_usage(sys.stderr)
        print(f"{Fore.RED}Error: {message}{Style.RESET_ALL}", file=sys.stderr)
        raise SystemExit(1)


def _format_group_help(parser: argparse.ArgumentParser) -> str:
    subcommands = getattr(parser, "group_subcommands", [])
    examples = getattr(parser, "group_examples", [])
    description = getattr(parser, "group_description", "")
    name = getattr(parser, "group_name", "")

    lines = [
        "NAME",
        f"{name}",
        "",
    ]
    if description:
        lines.extend(["DESCRIPTION", f"{description}", ""])
    if subcommands:
        lines.append("SUBCOMMANDS")
        for label, detail in subcommands:
            lines.append(f"{label:<12} {detail}")
        lines.append("")

    lines.extend(
        [
            "OPTIONS",
            "-h, --help    Show this help message",
            "",
        ]
    )

    if examples:
        lines.append("EXAMPLES")
        lines.extend(examples)
        lines.append("")

    return "\n".join(lines)


def _group_error(parser: argparse.ArgumentParser, message: str) -> None:
    if "invalid choice" in message and "argument scan_type" in message:
        invalid = message.split("invalid choice:", 1)[1].split("(", 1)[0].strip()
        invalid = invalid.strip("'\"")
        print(f"{Fore.RED}Error: invalid scan type '{invalid}'{Style.RESET_ALL}", file=sys.stderr)
        print("\nAvailable scan types:", file=sys.stderr)
        for name in getattr(parser, "scan_types", []):
            print(f"  {name}", file=sys.stderr)
        raise SystemExit(1)
    parser.print_usage(sys.stderr)
    print(f"{Fore.RED}Error: {message}{Style.RESET_ALL}", file=sys.stderr)
    raise SystemExit(1)


def _format_subcommand_help(parser: argparse.ArgumentParser) -> str:
    lines = []
    usage = getattr(parser, "_usage_text", "")
    description = getattr(parser, "_description_text", "")
    arguments = getattr(parser, "_arguments_text", "")
    options = getattr(parser, "_options_text", "")
    examples = getattr(parser, "_examples_text", "")

    if usage:
        lines.extend(["Usage:", f"  {usage}", ""])
    if description:
        lines.extend(["Description:", f"  {description}", ""])
    if arguments:
        lines.extend(["Arguments:", *[f"  {line}" for line in arguments.splitlines()], ""])
    if options:
        lines.extend(["Options:", *[f"  {line}" for line in options.splitlines()], ""])
    if examples:
        lines.extend(["Examples:", *[f"  {line}" for line in examples.splitlines()], ""])
    return "\n".join(lines)


def _subcommand_error(parser: argparse.ArgumentParser, message: str) -> None:
    if "the following arguments are required:" in message:
        required = message.split(":", 1)[1].strip()
        if "," in required:
            message = f"missing required arguments: {required}"
        else:
            message = f"missing required argument: {required}"
    print(f"{Fore.RED}Error: {message}{Style.RESET_ALL}", file=sys.stderr)
    usage = getattr(parser, "_usage_text", "")
    if usage:
        print("\nUsage:", file=sys.stderr)
        print(f"  {usage}", file=sys.stderr)
    raise SystemExit(1)


def _attach_group_help(
    parser: argparse.ArgumentParser,
    *,
    name: str,
    description: str,
    subcommands: list[tuple[str, str]],
    examples: list[str],
) -> None:
    parser.group_name = name
    parser.group_description = description
    parser.group_subcommands = subcommands
    parser.group_examples = examples
    parser.format_help = types.MethodType(lambda self: _format_group_help(self), parser)
    parser.error = types.MethodType(lambda self, msg: _group_error(self, msg), parser)


def _attach_subcommand_help(
    parser: argparse.ArgumentParser,
    *,
    description: str,
    usage: str,
    arguments: str,
    options: str,
    examples: str,
) -> None:
    parser._description_text = description
    parser._usage_text = usage
    parser._arguments_text = arguments
    parser._options_text = options
    parser._examples_text = examples
    parser.format_help = types.MethodType(lambda self: _format_subcommand_help(self), parser)
    parser.error = types.MethodType(lambda self, msg: _subcommand_error(self, msg), parser)


def _print_header() -> None:
    print(f"{Fore.MAGENTA}BlackHaven Framework v{VERSION}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Modular Cybersecurity Recon Framework{Style.RESET_ALL}")


def _build_parser() -> argparse.ArgumentParser:
    parser = BlackHavenArgumentParser(
        prog="blackhaven",
        add_help=True,
        description=f"BlackHaven Framework v{VERSION}\nModular Cybersecurity Recon Framework",
        formatter_class=argparse.RawTextHelpFormatter,
        usage="blackhaven <command> [options]",
    )

    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("-t", "--threads", type=int, help="Override thread count")
    parser.add_argument(
        "--generate-completion",
        action="store_true",
        help="Generate bash auto-completion script",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"BlackHaven Framework v{VERSION}",
    )

    subparsers = parser.add_subparsers(dest="command", required=False)

    scan = subparsers.add_parser("scan", help="Run reconnaissance modules")
    _attach_group_help(
        scan,
        name="blackhaven scan - run reconnaissance modules",
        description="Perform reconnaissance scans against a target domain or host.",
        subcommands=[
            ("domain", "Run domain reconnaissance"),
            ("ports", "Scan open ports"),
            ("subdomains", "Enumerate subdomains"),
            ("tech", "Detect technologies"),
        ],
        examples=[
            "blackhaven scan domain example.com",
            "blackhaven scan ports example.com",
            "blackhaven scan subdomains example.com",
            "blackhaven scan tech example.com",
        ],
    )
    scan_sub = scan.add_subparsers(dest="scan_type", required=True)
    scan.scan_types = ["domain", "ports", "subdomains", "tech"]
    scan_domain = scan_sub.add_parser("domain", help="Run domain reconnaissance")
    _attach_subcommand_help(
        scan_domain,
        description="Perform domain reconnaissance including DNS resolution and WHOIS lookup.",
        usage="blackhaven scan domain <target>",
        arguments="target      Domain to scan",
        options="-o, --output FILE     Save output to file\n-t, --threads INT     Number of threads",
        examples="blackhaven scan domain example.com",
    )
    scan_domain.add_argument("target")

    scan_ports = scan_sub.add_parser("ports", help="Scan ports")
    _attach_subcommand_help(
        scan_ports,
        description="Scan common ports on a target host.",
        usage="blackhaven scan ports <target>",
        arguments="target      Host or domain to scan",
        options="-o, --output FILE     Save output to file\n-t, --threads INT     Number of threads",
        examples="blackhaven scan ports example.com",
    )
    scan_ports.add_argument("target")

    scan_subdomains = scan_sub.add_parser("subdomains", help="Enumerate subdomains")
    _attach_subcommand_help(
        scan_subdomains,
        description="Enumerate subdomains using a configured wordlist.",
        usage="blackhaven scan subdomains <target>",
        arguments="target      Domain to enumerate",
        options="-o, --output FILE     Save output to file\n-t, --threads INT     Number of threads",
        examples="blackhaven scan subdomains example.com",
    )
    scan_subdomains.add_argument("target")

    scan_tech = scan_sub.add_parser("tech", help="Detect technologies")
    _attach_subcommand_help(
        scan_tech,
        description="Detect web technologies and CDN hints from HTTP headers.",
        usage="blackhaven scan tech <target>",
        arguments="target      Domain or URL to scan",
        options="-o, --output FILE     Save output to file",
        examples="blackhaven scan tech example.com",
    )
    scan_tech.add_argument("target")

    osint = subparsers.add_parser("osint", help="Run OSINT modules")
    _attach_group_help(
        osint,
        name="blackhaven osint - run OSINT modules",
        description="Perform ethical OSINT lookups on public data sources.",
        subcommands=[
            ("username", "Perform OSINT username lookup"),
        ],
        examples=[
            "blackhaven osint username johndoe",
        ],
    )
    osint_sub = osint.add_subparsers(dest="osint_type", required=True)
    osint_user = osint_sub.add_parser("username", help="Perform OSINT lookup")
    _attach_subcommand_help(
        osint_user,
        description="Check a username across common public platforms.",
        usage="blackhaven osint username <username>",
        arguments="username    Username to search",
        options="-o, --output FILE     Save output to file",
        examples="blackhaven osint username johndoe",
    )
    osint_user.add_argument("username")

    modules = subparsers.add_parser("modules", help="Manage modules")
    _attach_group_help(
        modules,
        name="blackhaven modules - manage modules",
        description="Inspect available modules and run specific modules.",
        subcommands=[
            ("list", "List available modules"),
            ("run", "Run a module"),
        ],
        examples=[
            "blackhaven modules list",
            "blackhaven modules run domain_recon example.com",
        ],
    )
    modules_sub = modules.add_subparsers(dest="modules_cmd", required=True)
    modules_list = modules_sub.add_parser("list", help="List available modules")
    _attach_subcommand_help(
        modules_list,
        description="List all available framework modules.",
        usage="blackhaven modules list",
        arguments="",
        options="",
        examples="blackhaven modules list",
    )
    modules_run = modules_sub.add_parser("run", help="Run a module")
    _attach_subcommand_help(
        modules_run,
        description="Run a specific module by name.",
        usage="blackhaven modules run <module> <target>",
        arguments="module      Module name\n"
        "target      Target for the module",
        options="-o, --output FILE     Save output to file\n-t, --threads INT     Number of threads",
        examples="blackhaven modules run domain_recon example.com",
    )
    modules_run.add_argument("module")
    modules_run.add_argument("target")

    session = subparsers.add_parser("session", help="Manage sessions")
    _attach_group_help(
        session,
        name="blackhaven session - manage sessions",
        description="Save, load, and list session data.",
        subcommands=[
            ("save", "Save current session"),
            ("load", "Load a session"),
            ("list", "List sessions"),
        ],
        examples=[
            "blackhaven session save daily-scan",
            "blackhaven session load daily-scan",
            "blackhaven session list",
        ],
    )
    session_sub = session.add_subparsers(dest="session_cmd", required=True)
    session_save = session_sub.add_parser("save", help="Save current session")
    _attach_subcommand_help(
        session_save,
        description="Save current session data under a name.",
        usage="blackhaven session save <name>",
        arguments="name        Session name",
        options="",
        examples="blackhaven session save daily-scan",
    )
    session_save.add_argument("name")
    session_load = session_sub.add_parser("load", help="Load a session")
    _attach_subcommand_help(
        session_load,
        description="Load a saved session by name.",
        usage="blackhaven session load <name>",
        arguments="name        Session name",
        options="",
        examples="blackhaven session load daily-scan",
    )
    session_load.add_argument("name")
    session_list = session_sub.add_parser("list", help="List sessions")
    _attach_subcommand_help(
        session_list,
        description="List available session files.",
        usage="blackhaven session list",
        arguments="",
        options="",
        examples="blackhaven session list",
    )

    report = subparsers.add_parser("report", help="Export reports")
    _attach_group_help(
        report,
        name="blackhaven report - export reports",
        description="Export JSON or HTML reports from the current results.",
        subcommands=[
            ("json", "Export JSON report"),
            ("html", "Export HTML report"),
        ],
        examples=[
            "blackhaven report json",
            "blackhaven report html",
        ],
    )
    report_sub = report.add_subparsers(dest="report_type", required=True)
    report_json = report_sub.add_parser("json", help="Export JSON report")
    _attach_subcommand_help(
        report_json,
        description="Export the current results as a JSON report.",
        usage="blackhaven report json",
        arguments="",
        options="-o, --output FILE     Save output to file",
        examples="blackhaven report json",
    )
    report_html = report_sub.add_parser("html", help="Export HTML report")
    _attach_subcommand_help(
        report_html,
        description="Export the current results as an HTML report.",
        usage="blackhaven report html",
        arguments="",
        options="-o, --output FILE     Save output to file",
        examples="blackhaven report html",
    )

    config = subparsers.add_parser("config", help="Show configuration")
    _attach_group_help(
        config,
        name="blackhaven config - show configuration",
        description="Display the current configuration values.",
        subcommands=[
            ("show", "Show configuration"),
        ],
        examples=[
            "blackhaven config show",
        ],
    )
    config_sub = config.add_subparsers(dest="config_cmd", required=True)
    config_show = config_sub.add_parser("show", help="Show configuration")
    _attach_subcommand_help(
        config_show,
        description="Display the current configuration values.",
        usage="blackhaven config show",
        arguments="",
        options="",
        examples="blackhaven config show",
    )

    return parser


def _print_completion_script() -> None:
    script = r"""_blackhaven_complete() {
  local cur prev opts
  COMPREPLY=()
  cur="${COMP_WORDS[COMP_CWORD]}"
  prev="${COMP_WORDS[COMP_CWORD-1]}"
  opts="scan osint modules session config report --help --generate-completion -o --output -v --verbose -t --threads --version"

  case "${prev}" in
    scan) COMPREPLY=( $(compgen -W "domain ports subdomains tech" -- "${cur}") ); return 0 ;;
    osint) COMPREPLY=( $(compgen -W "username" -- "${cur}") ); return 0 ;;
    modules) COMPREPLY=( $(compgen -W "list run" -- "${cur}") ); return 0 ;;
    session) COMPREPLY=( $(compgen -W "save load list" -- "${cur}") ); return 0 ;;
    config) COMPREPLY=( $(compgen -W "show" -- "${cur}") ); return 0 ;;
    report) COMPREPLY=( $(compgen -W "json html" -- "${cur}") ); return 0 ;;
  esac

  COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
  return 0
}
complete -F _blackhaven_complete blackhaven
"""
    print(script)


def _apply_global_overrides(framework: Framework, args: argparse.Namespace) -> None:
    if args.threads:
        framework.config.data["thread_count"] = args.threads


def _run_with_timing(label: str, action: Callable[[], None]) -> None:
    start = time.perf_counter()
    action()
    elapsed = time.perf_counter() - start
    print(f"{Fore.GREEN}{label} completed in {elapsed:.2f} seconds{Style.RESET_ALL}")


def _run_framework(args: argparse.Namespace) -> int:
    if args.generate_completion:
        _print_completion_script()
        return 0

    if not args.command:
        _build_parser().print_help()
        return 0

    framework = Framework()
    _apply_global_overrides(framework, args)

    if args.command == "scan":
        mapping = {
            "domain": "domain_recon",
            "ports": "port_scanner",
            "subdomains": "subdomain_enum",
            "tech": "tech_detection",
        }
        module_name = mapping.get(args.scan_type)
        if not module_name:
            print(f"{Fore.RED}Error: invalid scan type '{args.scan_type}'{Style.RESET_ALL}")
            print("\nAvailable scan types:")
            for name in mapping:
                print(f"  {name}")
            return 1
        _run_with_timing("Scan", lambda: framework.run_module(module_name, args.target))
        return 0

    if args.command == "osint" and args.osint_type == "username":
        _run_with_timing("OSINT scan", lambda: framework.run_module("osint_lookup", args.username))
        return 0

    if args.command == "modules":
        if args.modules_cmd == "list":
            for name in sorted(framework.modules.keys()):
                print(name)
            return 0
        if args.modules_cmd == "run":
            if args.module not in framework.modules:
                print(
                    f"{Fore.RED}Error: module '{args.module}' not found{Style.RESET_ALL}"
                )
                return 1
            _run_with_timing("Module run", lambda: framework.run_module(args.module, args.target))
            return 0

    if args.command == "session":
        if args.session_cmd == "save":
            path = framework.save_session(args.name)
            print(f"{Fore.GREEN}Session saved to {path}{Style.RESET_ALL}")
            return 0
        if args.session_cmd == "load":
            path = framework.load_session(args.name)
            print(f"{Fore.GREEN}Session loaded from {path}{Style.RESET_ALL}")
            return 0
        if args.session_cmd == "list":
            for name in framework.list_sessions():
                print(name)
            return 0

    if args.command == "config" and args.config_cmd == "show":
        framework._show_config()
        return 0

    if args.command == "report":
        if args.report_type == "json":
            if args.output:
                path = framework.save_report_json(args.output)
            else:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                path = framework.save_report_json(
                    f"{framework.output_dir}/blackhaven-results-{timestamp}.json"
                )
            print(f"{Fore.GREEN}JSON report saved to {path}{Style.RESET_ALL}")
            return 0
        if args.report_type == "html":
            path = framework.save_report_html(args.output)
            print(f"{Fore.GREEN}HTML report saved to {path}{Style.RESET_ALL}")
            return 0

    return 1


def main() -> int:
    require_legal_acknowledgement()
    updater.update()
    parser = _build_parser()
    args = parser.parse_args()
    if args.command:
        _print_header()
    try:
        return _run_framework(args)
    except SystemExit as exc:
        raise exc
    except Exception as exc:
        print(f"{Fore.RED}System error: {exc}{Style.RESET_ALL}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
