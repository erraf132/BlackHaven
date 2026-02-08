from __future__ import annotations

import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple

from colorama import Fore, Style

from ._utils import export_results, get_logger

LOG = get_logger("domain_info")

DOMAIN_RE = re.compile(r"^(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}$")


def _run_cmd(label: str, cmd: List[str]) -> Tuple[str, str]:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, check=False)
        if result.returncode == 0:
            return label, result.stdout.strip() or "No output"
        return label, f"Command failed (code {result.returncode})"
    except Exception as exc:
        LOG.exception("Command failed: %s", exc)
        return label, "Command failed"


def run() -> None:
    domain = input("Domain (example.com): ").strip()
    if not domain:
        print("No domain provided.")
        return
    if not DOMAIN_RE.fullmatch(domain):
        print("Invalid domain format.")
        return

    print("\nGathering domain info...")

    tasks = [
        ("WHOIS", ["whois", domain]),
        ("DNS A", ["nslookup", "-type=a", domain]),
        ("DNS NS", ["nslookup", "-type=ns", domain]),
        ("DNS MX", ["nslookup", "-type=mx", domain]),
    ]

    results: List[Tuple[str, str]] = []
    try:
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(_run_cmd, label, cmd) for label, cmd in tasks]
            for fut in as_completed(futures):
                results.append(fut.result())
    except Exception as exc:
        LOG.exception("Threaded info gathering failed: %s", exc)
        print("Error: failed during lookups. See ~/.blackhaven/results/blackhaven.log")
        return

    output_lines = [f"Domain: {domain}", ""]
    rows = [{"section": "Domain", "value": domain}]
    for label, output in results:
        print(f"{Fore.RED}{label}:{Style.RESET_ALL}")
        snippet = output if len(output) < 1200 else output[:1200] + "\n... (truncated)"
        print(snippet)
        print()
        output_lines.append(f"[{label}]")
        output_lines.append(output)
        output_lines.append("")
        rows.append({"section": label, "value": output})

    paths = export_results("domain_info", output_lines, rows)
    print("Saved results to:")
    for p in paths:
        print(f"- {p}")


def get_module():
    return {
        "name": "Domain Info",
        "description": "WHOIS and DNS records for a domain",
        "run": run,
    }
