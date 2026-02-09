"""
BlackHaven Framework
Copyright (c) 2026 erraf132 and Vyrn.exe Official
All rights reserved.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

from blackhaven.auth_pkg.db import (
    create_owner as _db_create_owner,
    get_machine_id,
    get_owner_record,
    get_owner_username,
    owner_exists as _db_owner_exists,
    verify_owner_login,
)
from blackhaven.auth_pkg.owner_registry import (
    claim_global_owner,
    release_global_owner,
    store_owner_token,
)
from blackhaven.auth_pkg.errors import OwnerAlreadyExistsError, OwnerRegistryError


class OwnerManager:
    """
    Singleton manager for the global owner account.

    This centralizes the "single owner" rule so every caller goes through
    the same checks. The SQLite database also enforces uniqueness with a
    partial unique index on the owner role, providing a second layer of safety.
    """

    _instance: Optional["OwnerManager"] = None

    def __new__(cls) -> "OwnerManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def owner_exists(self) -> bool:
        """Return True if an owner record already exists in storage."""
        return _db_owner_exists()

    def get_owner_username(self) -> Optional[str]:
        """Return the current owner's username if one exists."""
        return get_owner_username()

    def get_owner_record(self) -> Optional[Dict[str, str]]:
        """Return the current owner's full record if one exists."""
        return get_owner_record()

    def create_owner(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Create the global owner account.

        If an owner already exists, refuse the request with a clear error.
        """
        if self.owner_exists():
            raise OwnerAlreadyExistsError("Owner already exists. Cannot create another owner account.")
        try:
            ok, message, token = claim_global_owner(username, get_machine_id())
        except OwnerRegistryError as exc:
            return False, str(exc)
        if not ok:
            if "already exists" in message.lower():
                raise OwnerAlreadyExistsError("Owner already exists. Cannot create another owner account.")
            return False, message
        ok, message = _db_create_owner(username, password)
        if ok:
            if token:
                store_owner_token(token)
            return True, "Owner account created."
        release_global_owner()
        if "owner" in message.lower():
            raise OwnerAlreadyExistsError("Owner already exists. Cannot create another owner account.")
        return False, message

    def verify_owner(self, username: str, password: str) -> Tuple[bool, str]:
        """Verify an owner login against the stored credentials."""
        return verify_owner_login(username, password)
