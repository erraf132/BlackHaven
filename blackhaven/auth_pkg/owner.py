"""
BlackHaven Framework
Copyright (c) 2026 erraf132 and Vyrn.exe Official
All rights reserved.
"""



from __future__ import annotations

from typing import Dict, Optional, Tuple

from blackhaven.auth_pkg.db import (
    create_owner,
    get_machine_id,
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
    stored_machine_id = owner.get("machine_id")
    return bool(stored_machine_id and stored_machine_id == get_machine_id())


def is_owner(username: str) -> bool:
    owner_username = get_owner_username()
    return bool(owner_username and owner_username.lower() == username.lower())
