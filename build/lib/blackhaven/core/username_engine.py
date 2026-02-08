from __future__ import annotations

import json
import os
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

from blackhaven.utils.storage import save_json, save_text

_DEFAULT_TIMEOUT = 6.0


def _load_sites(path: str) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("sites", [])


def _check_status_code(url: str, timeout: float) -> int:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "BlackHaven/1.0"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=timeout) as resp:
        return resp.getcode()


def _check_site(site: Dict[str, str], username: str, timeout: float) -> Dict[str, str]:
    url = site["url"].format(username=username)
    name = site.get("name", url)
    check_type = site.get("check_type", "status_code")
    try:
        if check_type == "status_code":
            status = _check_status_code(url, timeout)
            found = status == 200
        else:
            status = _check_status_code(url, timeout)
            found = status == 200
        return {
            "site": name,
            "url": url,
            "status": str(status),
            "found": "yes" if found else "no",
        }
    except urllib.error.HTTPError as exc:
        return {
            "site": name,
            "url": url,
            "status": str(exc.code),
            "found": "no",
        }
    except Exception:
        return {
            "site": name,
            "url": url,
            "status": "error",
            "found": "no",
        }


def search_username(
    username: str,
    sites_path: str | None = None,
    max_workers: int = 20,
    timeout: float = _DEFAULT_TIMEOUT,
) -> List[Dict[str, str]]:
    if not sites_path:
        sites_path = os.path.join(os.path.dirname(__file__), "..", "data", "sites.json")
        sites_path = os.path.abspath(sites_path)

    sites = _load_sites(sites_path)
    results: List[Dict[str, str]] = []
    lock = threading.Lock()

    start = time.time()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_check_site, site, username, timeout) for site in sites]
        for future in as_completed(futures):
            result = future.result()
            with lock:
                results.append(result)

    duration = time.time() - start
    lines = [
        f"Username: {username}",
        f"Checked: {len(results)} sites",
        f"Duration: {duration:.2f}s",
        "",
    ]
    for entry in sorted(results, key=lambda x: x["site"].lower()):
        lines.append(f"{entry['site']}: {entry['url']} [{entry['status']}] found={entry['found']}")

    save_text(f"username_{username}", lines)
    save_json(f"username_{username}", results)
    return results
