#!/usr/bin/env python3
"""
BlackHaven Framework
Copyright (c) 2026 erraf132 and Vyrn.exe Official
All rights reserved.
"""




from __future__ import annotations

import json
import os
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple

import requests

SITES_PATH = "/home/hacker/WhatsMyName/blackbird/data.json"
RESULTS_DIR = "/home/hacker/BlackHaven/results/god_osint"
THREADS = 64
TIMEOUT = 5

_thread_local = threading.local()


def _ensure_dirs() -> None:
    os.makedirs("/home/hacker/BlackHaven/results", exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs("/home/hacker/BlackHaven/skills", exist_ok=True)


def _load_sites() -> List[Dict[str, str]]:
    with open(SITES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("sites", [])


def _format_url(template: str, username: str) -> str:
    return template.format_map({"account": username, "username": username})


def _session() -> requests.Session:
    session = getattr(_thread_local, "session", None)
    if session is None:
        session = requests.Session()
        _thread_local.session = session
    return session


def _check_site(site: Dict[str, str], username: str) -> Tuple[str, bool]:
    name = site.get("name", "unknown")
    template = site.get("uri_check")
    if not template:
        return name, False
    url = _format_url(template, username)
    try:
        resp = _session().get(url, timeout=TIMEOUT)
        return name, resp.status_code == 200
    except Exception:
        return name, False


def _save_results(username: str, found: List[str]) -> str:
    path = os.path.join(RESULTS_DIR, f"{username}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("GOD OSINT CORE Results\n")
        f.write(f"Username: {username}\n\n")
        for site in found:
            f.write(f"{site}\n")
    return path


def _stream_and_prefix(cmd: List[str], prefix: str) -> None:
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except FileNotFoundError:
        print(f"[{prefix}] ERROR: command not found")
        return

    if not proc.stdout:
        return

    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        if "FOUND" in line:
            print(f"[{prefix}] {line}")
    proc.wait()


def run_blackbird(username: str) -> None:
    cmd = [
        "/home/hacker/BlackHaven/venv/bin/python",
        "/home/hacker/WhatsMyName/blackbird/blackbird.py",
        "-u",
        username,
    ]
    _stream_and_prefix(cmd, "BLACKBIRD")


def run_sherlock(username: str) -> None:
    cmd = [
        "/home/hacker/BlackHaven/venv/bin/python",
        "-m",
        "sherlock",
        username,
    ]
    _stream_and_prefix(cmd, "SHERLOCK")


def run_god_core(username: str) -> List[str]:
    sites = _load_sites()
    found_sites: List[str] = []
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = [executor.submit(_check_site, site, username) for site in sites]
        for future in as_completed(futures):
            name, found = future.result()
            if found:
                print(f"[GOD CORE] FOUND: {name}")
                found_sites.append(name)
    return found_sites


def main() -> None:
    _ensure_dirs()
    username = input("Enter username: ").strip()
    if not username:
        print("No username provided.")
        return

    run_blackbird(username)
    run_sherlock(username)
    found = run_god_core(username)

    path = _save_results(username, found)
    print(f"\nResults saved: {path}")


if __name__ == "__main__":
    main()
