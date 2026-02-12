"""
BlackHaven Framework
Copyright (c) 2026 erraf132 and Vyrn.exe Official
All rights reserved.
"""



from __future__ import annotations

import os
import platform
import socket
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple

from colorama import Fore, Style

from ._utils import get_logger, save_result

LOG = get_logger("system_info")


def _uptime_seconds() -> str:
    try:
        with open("/proc/uptime", "r", encoding="utf-8") as f:
            seconds = float(f.read().split()[0])
        return str(int(seconds))
    except Exception:
        return "Unknown"


def _run_cmd(cmd: List[str]) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=6, check=False)
        if result.returncode == 0:
            return result.stdout.strip() or "No output"
        return "Command failed"
    except Exception as exc:
        LOG.exception("Command failed: %s", exc)
        return "Command failed"


def run() -> None:
    print("Gathering system info...")

    tasks = {
        "Hostname": socket.gethostname,
        "OS": platform.platform,
        "Kernel": platform.release,
        "Architecture": platform.machine,
        "Python": platform.python_version,
        "Uptime (sec)": _uptime_seconds,
        "User": lambda: os.getenv("USER") or os.getenv("USERNAME") or "Unknown",
        "IP Addresses": lambda: ", ".join({
            ip[4][0]
            for ip in socket.getaddrinfo(socket.gethostname(), None)
            if ":" not in ip[4][0]
        }) or "Unknown",
        "Current Time": lambda: time.strftime("%Y-%m-%d %H:%M:%S"),
        "Distro": lambda: _run_cmd(["lsb_release", "-d"]).replace("Description:\t", ""),
    }

    results: List[Tuple[str, str]] = []
    try:
        with ThreadPoolExecutor(max_workers=6) as pool:
            future_map = {pool.submit(fn): name for name, fn in tasks.items()}
            for fut in as_completed(future_map):
                name = future_map[fut]
                try:
                    results.append((name, str(fut.result())))
                except Exception as exc:
                    LOG.exception("Task failed: %s", exc)
                    results.append((name, "Error"))
    except Exception as exc:
        LOG.exception("System info failed: %s", exc)
        print("Error: failed to gather system info. See ~/.blackhaven/results/blackhaven.log")
        return

    results.sort(key=lambda x: x[0])

    output_lines = []
    for name, value in results:
        line = f"{name}: {value}"
        print(f"{Fore.RED}{name}:{Style.RESET_ALL} {value}")
        output_lines.append(line)

    path = save_result("system_info", output_lines)
    print(f"\nSaved results to: {path}")


def get_module():
    return {
        "name": "System Info",
        "description": "Local system information",
        "run": run,
    }
