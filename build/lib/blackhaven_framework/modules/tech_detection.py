"""Technology detection module (headers and CDN indicators)."""

from __future__ import annotations

from typing import Any, Dict

import requests

from core.utils import Output


CDN_SIGNATURES = {
    "cloudflare": ["cloudflare", "cf-ray", "cf-cache-status"],
    "akamai": ["akamai", "akamai-ghost"],
    "fastly": ["fastly", "x-served-by"],
    "cloudfront": ["cloudfront", "x-amz-cf-id"],
    "incapsula": ["incapsula", "x-cdn"],
}


def _detect_cdn(headers: Dict[str, str]) -> str | None:
    """Detect CDN provider by matching header signatures."""

    header_blob = " ".join(f"{k}:{v}" for k, v in headers.items()).lower()
    for provider, tokens in CDN_SIGNATURES.items():
        if any(token in header_blob for token in tokens):
            return provider
    return None


def run(target: str, config) -> Dict[str, Any]:
    """Detect technology details from HTTP headers."""

    url = target
    if not url.startswith("http"):
        url = f"https://{target}"

    Output.info(f"Requesting {url}...")
    timeout = config.get("timeout", 6)
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True)
    except requests.RequestException as exc:
        raise RuntimeError(f"HTTP request failed: {exc}")

    headers = {k.lower(): v for k, v in response.headers.items()}
    server = headers.get("server")
    powered_by = headers.get("x-powered-by")
    cdn = _detect_cdn(headers)

    detected = []
    if server:
        detected.append(f"server:{server}")
    if powered_by:
        detected.append(f"x-powered-by:{powered_by}")
    if cdn:
        detected.append(f"cdn:{cdn}")

    return {
        "target": target,
        "url": response.url,
        "status_code": response.status_code,
        "server": server,
        "x_powered_by": powered_by,
        "cdn": cdn,
        "headers": headers,
        "detected_technologies": detected,
    }


def register(framework) -> None:
    """Module entrypoint registration."""

    framework.register_module("tech_detection", run)
