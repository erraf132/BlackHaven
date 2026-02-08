from __future__ import annotations

import json
import urllib.request
from typing import Dict, Tuple

from ._utils import get_logger

LOG = get_logger("net")


def http_request(
    url: str,
    headers: Dict[str, str] | None = None,
    timeout: int = 8,
    method: str = "GET",
) -> Tuple[int, str]:
    req = urllib.request.Request(url, headers=headers or {}, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read().decode("utf-8", errors="replace")


def http_get(url: str, headers: Dict[str, str] | None = None, timeout: int = 8) -> Tuple[int, str]:
    try:
        return http_request(url, headers=headers, timeout=timeout, method="GET")
    except Exception as exc:
        LOG.exception("HTTP GET failed: %s", exc)
        raise


def http_head(url: str, headers: Dict[str, str] | None = None, timeout: int = 8) -> Tuple[int, str]:
    try:
        return http_request(url, headers=headers, timeout=timeout, method="HEAD")
    except Exception as exc:
        LOG.exception("HTTP HEAD failed: %s", exc)
        raise


def http_get_json(url: str, headers: Dict[str, str] | None = None, timeout: int = 8) -> Tuple[int, dict]:
    status, body = http_get(url, headers=headers, timeout=timeout)
    return status, json.loads(body)
