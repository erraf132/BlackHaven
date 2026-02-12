"""
BlackHaven Framework
Copyright (c) 2026 erraf132 and Vyrn.exe Official
All rights reserved.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Dict, Optional, Tuple

import requests

from blackhaven.auth_pkg.db import (
    get_machine_id,
    get_meta,
    get_or_create_install_id,
    set_meta,
)
from blackhaven.auth_pkg.errors import OwnerRegistryError


_REGISTRY_URL_KEYS = (
    "BH_OWNER_REGISTRY_URL",
    "BLACKHAVEN_OWNER_REGISTRY_URL",
)
_TOKEN_KEYS = (
    "BH_OWNER_TOKEN",
    "BLACKHAVEN_OWNER_TOKEN",
)
_TOKEN_SECRET_KEYS = (
    "BH_OWNER_TOKEN_SECRET",
    "BLACKHAVEN_OWNER_TOKEN_SECRET",
)

_META_OWNER_TOKEN = "global_owner_token"


def _get_env_value(keys: tuple[str, ...]) -> Optional[str]:
    for key in keys:
        value = os.getenv(key)
        if value:
            return value.strip()
    return None


def _registry_url() -> Optional[str]:
    url = _get_env_value(_REGISTRY_URL_KEYS)
    if not url:
        return None
    return url.rstrip("/")


def _token_secret() -> Optional[str]:
    return _get_env_value(_TOKEN_SECRET_KEYS)


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _b64url_decode(raw: str) -> bytes:
    padded = raw + "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(padded.encode("utf-8"))


def _sign_hs256(message: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).digest()
    return _b64url_encode(digest)


def _verify_hs256(message: bytes, signature: str, secret: str) -> bool:
    expected = _sign_hs256(message, secret)
    return hmac.compare_digest(expected, signature)


def get_stored_owner_token() -> Optional[str]:
    return get_meta(_META_OWNER_TOKEN)


def store_owner_token(token: str) -> None:
    set_meta(_META_OWNER_TOKEN, token)


def verify_owner_token(
    token: str,
    username: str,
    machine_id: str,
) -> Tuple[bool, str, Optional[Dict[str, str]]]:
    secret = _token_secret()
    if not secret:
        return False, "Owner token secret is not configured.", None
    parts = token.split(".")
    if len(parts) != 3:
        return False, "Invalid owner token format.", None
    header_b64, payload_b64, signature = parts
    try:
        header = json.loads(_b64url_decode(header_b64))
        payload = json.loads(_b64url_decode(payload_b64))
    except (json.JSONDecodeError, ValueError):
        return False, "Invalid owner token payload.", None
    if header.get("alg") != "HS256":
        return False, "Unsupported owner token algorithm.", None
    message = f"{header_b64}.{payload_b64}".encode("utf-8")
    if not _verify_hs256(message, signature, secret):
        return False, "Owner token signature verification failed.", None
    if payload.get("sub") != "owner":
        return False, "Owner token is not for owner creation.", None
    if payload.get("username", "").lower() != username.lower():
        return False, "Owner token username mismatch.", None
    if payload.get("machine_id") != machine_id:
        return False, "Owner token machine mismatch.", None
    now = int(time.time())
    exp = int(payload.get("exp") or 0)
    if exp and now > exp:
        return False, "Owner token has expired.", None
    return True, "Owner token verified.", payload


def check_global_owner_status() -> Tuple[bool, str]:
    """
    Return (exists, message) for the global owner registry.
    If registry is not configured, returns (False, message).
    """
    url = _registry_url()
    if not url:
        return False, "Global owner registry is not configured."
    try:
        response = requests.get(
            f"{url}/v1/owner/status",
            params={"install_id": get_or_create_install_id()},
            timeout=8,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise OwnerRegistryError(f"Unable to reach global owner registry: {exc}") from exc
    except ValueError:
        raise OwnerRegistryError("Invalid response from global owner registry.")
    if data.get("owner_exists") is True:
        return True, "A global owner already exists."
    return False, "No global owner detected."


def claim_global_owner(
    username: str,
    machine_id: str,
) -> Tuple[bool, str, Optional[str]]:
    """
    Claim the global owner slot.

    If registry is configured, uses server-side reservation.
    Otherwise, verifies a signed token provided via environment.
    """
    url = _registry_url()
    if url:
        payload = {
            "install_id": get_or_create_install_id(),
            "username": username,
            "machine_id": machine_id,
        }
        try:
            response = requests.post(
                f"{url}/v1/owner/claim",
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise OwnerRegistryError(f"Unable to reach global owner registry: {exc}") from exc
        except ValueError:
            raise OwnerRegistryError("Invalid response from global owner registry.")
        if data.get("owner_exists") is True:
            return False, "A global owner already exists.", None
        if data.get("ok") is False:
            return False, data.get("error") or "Owner reservation denied.", None
        token = data.get("token") or None
        return True, "Global owner reserved.", token

    token = _get_env_value(_TOKEN_KEYS)
    if not token:
        return False, (
            "Global owner registry is not configured. "
            "Set BH_OWNER_REGISTRY_URL or provide BH_OWNER_TOKEN."
        ), None
    ok, message, _payload = verify_owner_token(token, username, machine_id)
    if not ok:
        return False, message, None
    return True, "Owner token accepted.", token


def release_global_owner() -> None:
    """Best-effort release if local creation fails after a claim."""
    url = _registry_url()
    if not url:
        return
    try:
        requests.post(
            f"{url}/v1/owner/release",
            json={"install_id": get_or_create_install_id()},
            timeout=5,
        )
    except requests.RequestException:
        return
