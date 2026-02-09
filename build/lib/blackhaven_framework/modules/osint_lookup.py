"""OSINT username lookup module (public profiles only)."""

from __future__ import annotations

from typing import Any, Dict, List

import requests

from core.utils import Output


PLATFORMS = {
    "GitHub": "https://github.com/{username}",
    "GitLab": "https://gitlab.com/{username}",
    "Twitter": "https://twitter.com/{username}",
    "Reddit": "https://www.reddit.com/user/{username}",
    "Instagram": "https://www.instagram.com/{username}",
    "Facebook": "https://www.facebook.com/{username}",
    "YouTube": "https://www.youtube.com/@{username}",
    "Medium": "https://medium.com/@{username}",
    "Dev.to": "https://dev.to/{username}",
    "Keybase": "https://keybase.io/{username}",
    "Pinterest": "https://www.pinterest.com/{username}",
    "SoundCloud": "https://soundcloud.com/{username}",
}


def _check_profile(url: str, timeout: float) -> bool:
    """Check if a profile URL appears to exist."""

    headers = {"User-Agent": "BlackHavenFramework/1.0"}
    try:
        response = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
        if response.status_code in {405, 403}:
            response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
    except requests.RequestException:
        return False

    return response.status_code in {200, 301, 302}


def run(target: str, config) -> Dict[str, Any]:
    """Perform username existence checks across platforms."""

    Output.info("Checking username across platforms...")
    results: List[Dict[str, Any]] = []
    timeout = config.get("timeout", 6)

    for name, template in PLATFORMS.items():
        url = template.format(username=target)
        exists = _check_profile(url, timeout)
        status = "found" if exists else "not_found"
        Output.info(f"{name}: {status}")
        results.append({"platform": name, "url": url, "status": status})

    return {
        "username": target,
        "results": results,
        "count": len(results),
    }


def register(framework) -> None:
    """Module entrypoint registration."""

    framework.register_module("osint_lookup", run)
