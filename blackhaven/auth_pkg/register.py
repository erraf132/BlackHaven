from __future__ import annotations

from typing import Tuple

from blackhaven.auth_pkg.db import register_user


def create_user(username: str, password: str) -> Tuple[bool, str, str]:
    return register_user(username, password, role="user")
