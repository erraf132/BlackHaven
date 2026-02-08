from __future__ import annotations

from typing import Dict, Optional, Tuple

from blackhaven.database import (
    create_owner,
    get_machine_fingerprint,
    get_owner_record,
    get_owner_username,
    owner_exists,
    verify_owner_login,
)


def load_owner() -> Optional[Dict[str, str]]:
    return get_owner_record()


def verify_owner(username: str, password: str) -> Tuple[bool, str]:
    return verify_owner_login(username, password)


def verify_owner_access(username: str) -> bool:
    owner = get_owner_record()
    if not owner:
        return False
    if owner.get("username", "").lower() != username.lower():
        return False
    fingerprint = get_machine_fingerprint()
    return (
        owner.get("hostname") == fingerprint["hostname"]
        and owner.get("machine_id") == fingerprint["machine_id"]
    )


def is_owner(username: str) -> bool:
    owner_username = get_owner_username()
    return bool(owner_username and owner_username.lower() == username.lower())
