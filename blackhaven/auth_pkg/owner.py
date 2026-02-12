"""
BlackHaven Framework
Copyright (c) 2026 erraf132 and Vyrn.exe Official
All rights reserved.
"""



from __future__ import annotations

from typing import Dict, Optional, Tuple

from blackhaven.auth_pkg.db import get_machine_id
from blackhaven.auth_pkg.owner_manager import OwnerManager
from blackhaven.auth_pkg.owner_registry import check_global_owner_status
from blackhaven.auth_pkg.errors import OwnerRegistryError


def load_owner() -> Optional[Dict[str, str]]:
    return OwnerManager().get_owner_record()


def owner_exists() -> bool:
    """Return True if a global owner already exists."""
    return OwnerManager().owner_exists()


def global_owner_exists() -> Tuple[bool, str]:
    """Check if a global owner exists via registry."""
    try:
        return check_global_owner_status()
    except OwnerRegistryError as exc:
        return False, str(exc)


def create_owner(username: str, password: str) -> Tuple[bool, str]:
    """Create the global owner account."""
    return OwnerManager().create_owner(username, password)


def verify_owner(username: str, password: str) -> Tuple[bool, str]:
    return OwnerManager().verify_owner(username, password)


def verify_owner_access(username: str) -> bool:
    owner = OwnerManager().get_owner_record()
    if not owner:
        return False
    if owner.get("username", "").lower() != username.lower():
        return False
    stored_machine_id = owner.get("machine_id")
    return bool(stored_machine_id and stored_machine_id == get_machine_id())


def is_owner(username: str) -> bool:
    owner_username = OwnerManager().get_owner_username()
    return bool(owner_username and owner_username.lower() == username.lower())
