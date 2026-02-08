from __future__ import annotations

from typing import Dict, List, Tuple

from blackhaven.auth_pkg.db import authenticate, list_users as db_list_users


def verify_login(username: str, password: str) -> Tuple[bool, str, str]:
    return authenticate(username, password)


def list_users() -> List[Dict[str, str]]:
    return db_list_users()
