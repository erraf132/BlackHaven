from __future__ import annotations

import json
import os
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Tuple

_DEFAULT_TIMEOUT = 6.0
_DEFAULT_SITES_PATH = os.path.expanduser("~/WhatsMyName/blackbird/sites.json")
_DEFAULT_MIN_WORKERS = 10
_DEFAULT_MAX_WORKERS = 30
_DEFAULT_WORKERS = 20
_USERNAME_RESULTS_DIR = "/home/hacker/BlackHaven/results/usernames"


def _load_sites(path: str) -> List[Dict[str, str]]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Sites file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("sites", [])


def _ensure_username_results_dir() -> None:
    os.makedirs(_USERNAME_RESULTS_DIR, exist_ok=True)


def _save_text(name: str, lines: List[str]) -> str:
    _ensure_username_results_dir()
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(ch for ch in name if ch.isalnum() or ch in ("-", "_"))
    path = os.path.join(_USERNAME_RESULTS_DIR, f"{safe_name}_{stamp}.txt")
    with open(path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line.rstrip("\n") + "\n")
    return path


def _save_json(name: str, data: object) -> str:
    _ensure_username_results_dir()
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(ch for ch in name if ch.isalnum() or ch in ("-", "_"))
    path = os.path.join(_USERNAME_RESULTS_DIR, f"{safe_name}_{stamp}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path


def _format_template(template: str, username: str) -> str:
    return template.format_map({"account": username, "username": username})


def _fetch_site(url: str, headers: Dict[str, str], body: str | None, timeout: float) -> Tuple[int, str]:
    method = "POST" if body is not None else "GET"
    payload = body.encode("utf-8") if body is not None else None
    request = urllib.request.Request(
        url,
        headers=headers,
        data=payload,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            status = resp.getcode()
            text = resp.read().decode("utf-8", errors="ignore")
            return status, text
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="ignore")
        return exc.code, text


def _check_site(site: Dict[str, str], username: str, timeout: float) -> Dict[str, str]:
    url_template = site.get("url") or site.get("uri_check")
    if not url_template:
        return {"site": site.get("name", "unknown"), "url": "", "status": "error", "found": "no"}

    display_template = site.get("uri_pretty") or url_template
    name = site.get("name", display_template)
    url = _format_template(url_template, username)
    display_url = _format_template(display_template, username)

    headers = {"User-Agent": "BlackHaven/1.0"}
    headers.update(site.get("headers", {}))
    body = site.get("post_body")
    if body is not None:
        body = _format_template(body, username)

    try:
        status, text = _fetch_site(url, headers, body, timeout)
        e_string = site.get("e_string")
        m_string = site.get("m_string")
        e_code = site.get("e_code")
        m_code = site.get("m_code")

        found: bool | None = None
        if m_string and m_string in text:
            found = False
        elif e_string and e_string in text:
            found = True

        if found is None:
            if m_code is not None and status == m_code:
                found = False
            elif e_code is not None and status == e_code:
                found = True
            else:
                found = status == 200

        return {
            "site": name,
            "url": display_url,
            "status": str(status),
            "found": "yes" if found else "no",
        }
    except urllib.error.HTTPError as exc:
        return {
            "site": name,
            "url": display_url,
            "status": str(exc.code),
            "found": "no",
        }
    except Exception:
        return {
            "site": name,
            "url": display_url,
            "status": "error",
            "found": "no",
        }


def search_username(
    username: str,
    sites_path: str | None = None,
    max_workers: int = _DEFAULT_WORKERS,
    timeout: float = _DEFAULT_TIMEOUT,
) -> List[Dict[str, str]]:
    if not sites_path:
        sites_path = _DEFAULT_SITES_PATH

    sites = _load_sites(sites_path)
    max_workers = max(_DEFAULT_MIN_WORKERS, min(_DEFAULT_MAX_WORKERS, max_workers))
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

    _save_text(f"username_{username}", lines)
    _save_json(f"username_{username}", results)
    return results
