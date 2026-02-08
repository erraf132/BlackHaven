from __future__ import annotations

import json
import os
from typing import Dict, List, Tuple

import bcrypt


def _users_path() -> str:
    base_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    return os.path.abspath(os.path.join(base_dir, "users.json"))


def _load_users() -> List[Dict[str, str]]:
    path = _users_path()
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("users", [])


def verify_login(username: str, password: str) -> Tuple[bool, str, str]:
    users = _load_users()
    for user in users:
        if user["username"].lower() == username.lower():
            stored = user.get("password_hash", "")
            if stored and bcrypt.checkpw(password.encode("utf-8"), stored.encode("utf-8")):
                return True, "Login successful.", user.get("role", "user")
            return False, "Invalid username or password.", "user"
    return False, "Invalid username or password.", "user"


def list_users() -> List[Dict[str, str]]:
    return _load_users()
