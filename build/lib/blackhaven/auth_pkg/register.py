from __future__ import annotations

import json
import os
from datetime import datetime
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


def _save_users(users: List[Dict[str, str]]) -> None:
    path = _users_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"users": users}, f, indent=2)


def create_user(username: str, password: str) -> Tuple[bool, str, str]:
    users = _load_users()
    if any(u["username"].lower() == username.lower() for u in users):
        return False, "Username already exists.", "user"

    role = "user"
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    users.append({
        "username": username,
        "password_hash": password_hash,
        "role": role,
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    })
    _save_users(users)
    return True, "Account created.", role
