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
from typing import Dict, Iterable, List, Set, Tuple

import requests

SITES_PATH = "/home/hacker/WhatsMyName/blackbird/data.json"
RESULTS_DIR = "/home/hacker/BlackHaven/results/omega"
THREADS = 128
TIMEOUT = 5

_thread_local = threading.local()


def _ensure_dirs() -> None:
    os.makedirs("/home/hacker/BlackHaven/skills", exist_ok=True)
    os.makedirs("/home/hacker/BlackHaven/results", exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)


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


def _check_site(site: Dict[str, str], username: str) -> Tuple[str, str] | None:
    name = site.get("name", "unknown")
    template = site.get("uri_check")
    if not template:
        return None
    url = _format_url(template, username)
    try:
        resp = _session().get(url, timeout=TIMEOUT, allow_redirects=False)
        if resp.status_code in {200, 301, 302}:
            return name, url
    except Exception:
        return None
    return None


def _save_results(username: str, urls: Iterable[str]) -> str:
    path = os.path.join(RESULTS_DIR, f"{username}.txt")
    with open(path, "w", encoding="utf-8") as f:
        for url in urls:
            f.write(f"[FOUND] [{url}]({url})\n")
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


def generate_variations(username: str) -> List[str]:
    base = [
        username,
        f"{username}_",
        f"{username}123",
        f"{username}01",
        f"{username}1",
        f"{username}.real",
        f"real.{username}",
        f"{username}_official",
        f"official_{username}",
        f"{username}.x",
        f"x.{username}",
        f"{username}0",
        f"{username}2",
        f"{username}007",
        f"{username}2024",
        f"{username}2025",
        f"{username}2026",
        f"the{username}",
        f"{username}the",
        f"{username}_dev",
        f"dev_{username}",
        f"{username}.dev",
        f"{username}_hq",
    ]
    return base


def expand_usernames(username: str) -> List[str]:
    variations: List[str] = []
    for i in range(1000):
        variations.append(f"{username}{i}")
        variations.append(f"{username}_{i}")
        variations.append(f"{username}.{i}")
        if len(variations) >= 100:
            break
    return variations[:100]


def _dedupe(items: Iterable[str]) -> List[str]:
    seen: Set[str] = set()
    output: List[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output


def run_custom_scan(username: str) -> List[str]:
    sites = _load_sites()
    found_urls: List[str] = []
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = [executor.submit(_check_site, site, username) for site in sites]
        for future in as_completed(futures):
            result = future.result()
            if not result:
                continue
            name, url = result
            print(f"[OMEGA] FOUND: {name}")
            found_urls.append(url)
    return found_urls


def main() -> None:
    _ensure_dirs()
    username = input("Enter username: ").strip()
    if not username:
        print("No username provided.")
        return

    print(f"[OMEGA] scanning username {username}")
    run_blackbird(username)
    run_sherlock(username)

    variations = _dedupe(generate_variations(username) + expand_usernames(username))
    all_found: List[str] = []
    for variation in variations:
        print(f"[OMEGA] checking variation: {variation}")
        all_found.extend(run_custom_scan(variation))

    path = _save_results(username, _dedupe(all_found))
    print(f"\nResults saved: {path}")


if __name__ == "__main__":
    main()
