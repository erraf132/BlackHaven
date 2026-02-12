"""
BlackHaven Framework
Copyright (c) 2026 erraf132 and Vyrn.exe Official
All rights reserved.
"""



from __future__ import annotations

import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Set

from colorama import Fore, Style

from blackhaven.auth_pkg.logger import log_action
from blackhaven.auth_pkg.session import get_current_user
from ._utils import export_results, get_logger

LOG = get_logger("port_scanner")


def _parse_ports(raw: str) -> List[int]:
    ports: Set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            start, end = int(start_s), int(end_s)
            for p in range(start, end + 1):
                if 1 <= p <= 65535:
                    ports.add(p)
        else:
            p = int(part)
            if 1 <= p <= 65535:
                ports.add(p)
    return sorted(ports)


def _scan_port(host: str, port: int, timeout: float) -> int | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            if result == 0:
                return port
    except Exception as exc:
        LOG.debug("Port scan error %s:%s: %s", host, port, exc)
    return None


def run() -> None:
    target = input("Target IP or hostname: ").strip()
    if not target:
        print("No target provided.")
        return

    ports_raw = input("Ports (e.g. 22,80,443 or 1-1024): ").strip()
    if not ports_raw:
        print("No ports provided.")
        return

    try:
        ports = _parse_ports(ports_raw)
        if not ports:
            print("No valid ports provided.")
            return
    except Exception:
        print("Invalid port format.")
        return

    try:
        ipaddress.ip_address(target)
    except ValueError:
        pass

    user = get_current_user()
    if user:
        log_action(user.username, f"port scan {target} ports={ports_raw}")

    print(f"\nScanning {target} ({len(ports)} ports)...")

    open_ports: List[int] = []
    try:
        with ThreadPoolExecutor(max_workers=200) as pool:
            futures = [pool.submit(_scan_port, target, p, 0.6) for p in ports]
            for fut in as_completed(futures):
                port = fut.result()
                if port is not None:
                    open_ports.append(port)
    except Exception as exc:
        LOG.exception("Port scan failed: %s", exc)
        print("Error: scan failed. See ~/.blackhaven/results/blackhaven.log")
        return

    open_ports.sort()
    output_lines = [f"Target: {target}", f"Ports scanned: {len(ports)}", ""]
    rows = [
        {"field": "Target", "value": target},
        {"field": "Ports scanned", "value": str(len(ports))},
    ]

    if open_ports:
        print(f"{Fore.GREEN}Open ports:{Style.RESET_ALL}")
        for p in open_ports:
            print(f"- {p}")
            output_lines.append(f"OPEN: {p}")
            rows.append({"field": "Open port", "value": str(p)})
    else:
        print(f"{Fore.RED}No open ports found.{Style.RESET_ALL}")
        output_lines.append("No open ports found")
        rows.append({"field": "Open ports", "value": "None"})

    paths = export_results("port_scanner", output_lines, rows)
    print("\nSaved results to:")
    for p in paths:
        print(f"- {p}")


def get_module():
    return {
        "name": "Port Scanner",
        "description": "Multithreaded TCP port scanner",
        "run": run,
    }
