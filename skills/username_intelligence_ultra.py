#!/usr/bin/env python3
"""
BlackHaven Framework
Copyright (c) 2026 erraf132 and Vyrn.exe Official
All rights reserved.
"""




from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple

MIN_THREADS = 32
TIMEOUT = 5

SITES_PATH = "/home/hacker/WhatsMyName/blackbird/data.json"
RESULTS_DIR = "/home/hacker/BlackHaven/results/usernames"


def _ensure_results_dir() -> None:
    os.makedirs(RESULTS_DIR, exist_ok=True)


def _load_sites() -> List[Dict[str, str]]:
    with open(SITES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("sites", [])


def _format_url(template: str, username: str) -> str:
    return template.format_map({"account": username, "username": username})


def _fetch(url: str) -> int:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "BlackHaven/2.0"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT) as resp:
        return resp.getcode()


def _check_site(site: Dict[str, str], username: str) -> Tuple[str, bool]:
    name = site.get("name", "unknown")
    template = site.get("uri_check")
    if not template:
        return name, False
    url = _format_url(template, username)
    try:
        status = _fetch(url)
        return name, status == 200
    except urllib.error.HTTPError as exc:
        return name, exc.code == 200
    except Exception:
        return name, False


def _save_results(username: str, results: List[Tuple[str, bool]]) -> str:
    _ensure_results_dir()
    path = os.path.join(RESULTS_DIR, f"{username}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("Username Intelligence ULTRA Results\n")
        f.write(f"Username: {username}\n\n")
        for site, found in results:
            status = "FOUND" if found else "NOT FOUND"
            f.write(f"{site}: {status}\n")
    return path


def scan(username: str) -> None:
    sites = _load_sites()
    threads = max(MIN_THREADS, 32)

    print(f"[+] Scanning username: {username}")
    print(f"[+] Threads: {threads}")
    print(f"[+] Sites: {len(sites)}\n")

    results: List[Tuple[str, bool]] = []
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(_check_site, site, username) for site in sites]
        for future in as_completed(futures):
            name, found = future.result()
            if found:
                print(f"[+] FOUND: {name}")
            else:
                print(f"[-] NOT FOUND: {name}")
            results.append((name, found))

    path = _save_results(username, results)
    print(f"\n[+] Results saved: {path}")


def main() -> None:
    username = input("Enter username: ").strip()
    if not username:
        print("No username provided.")
        return
    scan(username)


if __name__ == "__main__":
    main()
