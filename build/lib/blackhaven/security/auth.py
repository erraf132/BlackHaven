from __future__ import annotations

import getpass
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from typing import Dict, List, Optional

from blackhaven.auth_pkg.session import SessionUser, set_current_user


OWNER_USERNAME = "hacker"


def _security_dir() -> str:
    return os.path.abspath(os.path.dirname(__file__))


def _users_path() -> str:
    return os.path.join(_security_dir(), "users.json")


def _sessions_path() -> str:
    return os.path.join(_security_dir(), "sessions.log")


def _ensure_storage() -> None:
    os.makedirs(_security_dir(), exist_ok=True)
    if not os.path.isfile(_users_path()):
        _save_users({})
    if not os.path.isfile(_sessions_path()):
        with open(_sessions_path(), "a", encoding="utf-8") as f:
            f.write("")


def _load_users() -> Dict[str, Dict[str, str]]:
    _ensure_storage()
    try:
        with open(_users_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def _save_users(users: Dict[str, Dict[str, str]]) -> None:
    with open(_users_path(), "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)


def _timestamp() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _hash_password(password: str, salt: Optional[str] = None) -> str:
    if salt is None:
        salt = os.urandom(16).hex()
    digest = sha256((salt + password).encode("utf-8")).hexdigest()
    return f"sha256${salt}${digest}"


def _verify_password(stored_hash: str, password: str) -> bool:
    try:
        algo, salt, digest = stored_hash.split("$", 2)
    except ValueError:
        return False
    if algo != "sha256":
        return False
    return _hash_password(password, salt) == stored_hash


def list_users() -> List[Dict[str, str]]:
    users = _load_users()
    result = []
    for username, info in users.items():
        result.append(
            {
                "username": username,
                "role": info.get("role", "user"),
                "created_at": info.get("created", ""),
            }
        )
    result.sort(key=lambda x: x["username"].lower())
    return result


def read_users_json() -> str:
    _ensure_storage()
    try:
        with open(_users_path(), "r", encoding="utf-8") as f:
            return f.read().strip() or "{}"
    except Exception:
        return "{}"


def read_session_log(limit: Optional[int] = None) -> str:
    _ensure_storage()
    try:
        with open(_sessions_path(), "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        return "No session logs found."
    if limit:
        lines = lines[-limit:]
    return "".join(lines).strip() or "No session logs found."


def log_session(username: str, module_used: str) -> None:
    _ensure_storage()
    line = f"[{_timestamp()}] {username} | {module_used}\n"
    with open(_sessions_path(), "a", encoding="utf-8") as f:
        f.write(line)


def can_access_admin(username: str) -> bool:
    users = _load_users()
    info = users.get(username)
    if not info:
        return False
    return info.get("role") == "owner"


def _create_user(username: str, password: str) -> bool:
    users = _load_users()
    if username in users:
        return False
    role = "owner" if username == OWNER_USERNAME else "user"
    users[username] = {
        "password_hash": _hash_password(password),
        "created": _timestamp(),
        "role": role,
    }
    _save_users(users)
    return True


def _authenticate(username: str, password: str) -> Optional[str]:
    users = _load_users()
    info = users.get(username)
    if not info:
        return None
    stored = info.get("password_hash", "")
    if not stored:
        return None
    if _verify_password(stored, password):
        return info.get("role", "user")
    return None


def _menu_choice() -> str:
    print("1. Login")
    print("2. Create account")
    print("3. Exit")
    return input("Select an option: ").strip()


def require_login() -> SessionUser:
    _ensure_storage()
    while True:
        choice = _menu_choice()
        if choice == "3":
            raise SystemExit(0)
        if choice == "2":
            username = input("Username: ").strip()
            password = getpass.getpass("Password: ").strip()
            confirm = getpass.getpass("Confirm Password: ").strip()
            if not username or not password:
                print("Username and password are required.\n")
                continue
            if password != confirm:
                print("Passwords do not match.\n")
                continue
            if _create_user(username, password):
                role = "owner" if username == OWNER_USERNAME else "user"
                user = SessionUser(username=username, role=role)
                set_current_user(user.username, user.role)
                log_session(user.username, "login")
                return user
            print("Username already exists.\n")
            continue
        if choice == "1":
            username = input("Username: ").strip()
            password = getpass.getpass("Password: ").strip()
            role = _authenticate(username, password)
            if role:
                user = SessionUser(username=username, role=role)
                set_current_user(user.username, user.role)
                log_session(user.username, "login")
                return user
            print("Invalid username or password.\n")
            continue
        print("Invalid option.\n")


__all__ = [
    "OWNER_USERNAME",
    "can_access_admin",
    "list_users",
    "log_session",
    "read_session_log",
    "read_users_json",
    "require_login",
]
