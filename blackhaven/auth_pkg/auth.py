"""
BlackHaven Framework
Copyright (c) 2026 erraf132 and Vyrn.exe Official
All rights reserved.
"""



from __future__ import annotations

from typing import Tuple

from blackhaven.auth_pkg.login import verify_login
from blackhaven.auth_pkg.owner import (
    is_owner,
    load_owner,
    owner_exists,
    create_owner,
    verify_owner,
    verify_owner_access,
)
from blackhaven.auth_pkg.register import create_user
from blackhaven.auth_pkg.session import set_current_user
from blackhaven.auth_pkg.db import get_machine_id
from blackhaven.modules._utils import ensure_results_dir

import os
from datetime import datetime


_SECURITY_LOG = os.path.join(os.path.expanduser("~"), ".blackhaven", "results", "security.log")


def _log_security_event(action: str, username: str, outcome: str) -> None:
    ensure_results_dir()
    stamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {action} username={username} outcome={outcome}\n"
    with open(_SECURITY_LOG, "a", encoding="utf-8") as f:
        f.write(line)


def ensure_owner(username: str, password: str) -> Tuple[bool, str]:
    if owner_exists():
        _log_security_event("owner_create", username, "denied_existing_owner")
        return False, "Owner already exists."
    ok, message = create_owner(username, password)
    if ok:
        _log_security_event("owner_create", username, "success")
    else:
        _log_security_event("owner_create", username, "denied_locked")
    return ok, message


def authenticate(username: str, password: str) -> Tuple[bool, str, str]:
    if owner_exists() and is_owner(username):
        ok, message = verify_owner(username, password)
        if ok:
            owner = load_owner()
            stored_machine_id = owner.get("machine_id") if owner else None
            current_machine = get_machine_id()
            if not stored_machine_id or stored_machine_id != current_machine:
                ok = False
                message = "Owner account is locked to this machine."
        _log_security_event("login", username, "success" if ok else f"failure:{message}")
        if ok:
            set_current_user(username, "owner")
        return ok, message, "owner"
    ok, message, role = verify_login(username, password)
    _log_security_event("login", username, "success" if ok else f"failure:{message}")
    if ok:
        set_current_user(username, role)
    return ok, message, role


def can_access_admin(username: str) -> bool:
    return verify_owner_access(username)


def register_user(username: str, password: str) -> Tuple[bool, str, str]:
    owner = load_owner()
    if owner and owner.get("username", "").lower() == username.lower():
        return False, "Username is reserved.", "user"
    return create_user(username, password)
