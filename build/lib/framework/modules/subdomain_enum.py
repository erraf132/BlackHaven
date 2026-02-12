"""Subdomain enumeration module with built-in wordlist."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

from framework.core.utils import Output, safe_resolve


DEFAULT_WORDLIST = [
    "www", "mail", "ftp", "api", "dev", "staging", "test", "portal", "vpn", "admin",
    "beta", "blog", "cdn", "assets", "static", "img", "images", "secure", "shop", "store",
    "support", "docs", "status", "monitor", "auth", "sso", "gateway", "edge", "mx", "ns1",
    "ns2", "intranet", "git", "gitlab", "jenkins", "ci", "jira", "confluence", "help",
]


def _resolve_subdomain(domain: str, sub: str) -> Dict[str, str] | None:
    """Resolve a subdomain to an IP address."""

    host = f"{sub}.{domain}"
    ip = safe_resolve(host)
    if ip:
        return {"host": host, "ip": ip}
    return None


def _load_wordlist(config) -> List[str]:
    """Load a wordlist from config or use the built-in list."""

    wordlist = config.get("default_wordlist", DEFAULT_WORDLIST)
    if isinstance(wordlist, list):
        return wordlist

    if isinstance(wordlist, str):
        try:
            with open(wordlist, "r", encoding="utf-8") as handle:
                return [line.strip() for line in handle if line.strip()]
        except Exception:
            return DEFAULT_WORDLIST

    return DEFAULT_WORDLIST


def run(target: str, config) -> Dict[str, Any]:
    """Enumerate subdomains using a built-in wordlist."""

    wordlist = _load_wordlist(config)
    max_workers = config.get("thread_count", 50)
    Output.info("Enumerating subdomains...")
    found: List[Dict[str, str]] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_resolve_subdomain, target, sub): sub for sub in wordlist}
        total = len(futures)
        completed = 0
        for future in as_completed(futures):
            completed += 1
            Output.progress(f"Progress: {completed}/{total} subdomains checked")
            result = future.result()
            if result:
                found.append(result)
                Output.success(f"Found {result['host']} -> {result['ip']}")

    print()
    found.sort(key=lambda item: item["host"])
    return {
        "target": target,
        "found": found,
        "count": len(found),
    }


def register(framework) -> None:
    """Module entrypoint registration."""

    framework.register_module("subdomain_enum", run)
