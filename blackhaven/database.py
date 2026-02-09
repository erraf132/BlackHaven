"""
BlackHaven Framework
Copyright (c) 2026 erraf132 and Vyrn.exe Official
All rights reserved.
"""



from __future__ import annotations

import hashlib
import os
import platform
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Tuple

import bcrypt

_BASE_DIR = os.path.expanduser("~/.blackhaven")
_DB_PATH = os.path.join(_BASE_DIR, "users.db")
_LOGS_DIR = os.path.join(_BASE_DIR, "logs")
_MODULES_RESULTS_DIR = os.path.join(_BASE_DIR, "modules_results")

_ALLOWED_ROLES = {"owner", "admin", "user"}


@dataclass
class SessionUser:
    username: str
    role: str
    user_id: Optional[int] = None


_current_user: Optional[SessionUser] = None


def _utc_now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _ensure_storage() -> None:
    os.makedirs(_BASE_DIR, mode=0o700, exist_ok=True)
    os.makedirs(_LOGS_DIR, mode=0o700, exist_ok=True)
    os.makedirs(_MODULES_RESULTS_DIR, mode=0o700, exist_ok=True)
    try:
        os.chmod(_BASE_DIR, 0o700)
    except OSError:
        pass


def _connect() -> sqlite3.Connection:
    _ensure_storage()
    created = not os.path.exists(_DB_PATH)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    _init_db(conn)
    if created:
        try:
            os.chmod(_DB_PATH, 0o600)
        except OSError:
            pass
    return conn


def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('owner', 'admin', 'user')),
            created_at TEXT NOT NULL,
            machine_id TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            module TEXT NOT NULL,
            login_time TEXT NOT NULL,
            logout_time TEXT,
            success INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS security (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            event TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
        )
        """
    )
    try:
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_single_owner "
            "ON users(role) WHERE role = 'owner'"
        )
    except sqlite3.OperationalError:
        pass
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_activity_user_id ON activity(user_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_security_user_id ON security(user_id)"
    )
    conn.commit()


def get_machine_id() -> str:
    raw = (
        platform.node()
        + platform.system()
        + platform.release()
        + platform.processor()
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_machine_fingerprint() -> Dict[str, str]:
    return {
        "hostname": platform.node(),
        "machine_id": get_machine_id(),
    }


def set_current_user(username: str, role: str, user_id: Optional[int] = None) -> None:
    global _current_user
    _current_user = SessionUser(username=username, role=role, user_id=user_id)


def get_current_user() -> Optional[SessionUser]:
    return _current_user


def clear_session() -> None:
    global _current_user
    _current_user = None


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, stored_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))


def owner_exists() -> bool:
    with _connect() as conn:
        row = conn.execute(
            "SELECT id FROM users WHERE role = 'owner' LIMIT 1"
        ).fetchone()
        return row is not None


def get_owner_username() -> Optional[str]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT username FROM users WHERE role = 'owner' LIMIT 1"
        ).fetchone()
        return row["username"] if row else None


def get_owner_record() -> Optional[Dict[str, str]]:
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT id, username, role, created_at, machine_id
            FROM users WHERE role = 'owner' LIMIT 1
            """
        ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "username": row["username"],
            "role": row["role"],
            "created_at": row["created_at"],
            "machine_id": row["machine_id"],
        }


def _get_user_by_username(conn: sqlite3.Connection, username: str) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT id, username, password_hash, role, machine_id FROM users WHERE username = ?",
        (username,),
    ).fetchone()


def register_user(
    username: str,
    password: str,
    role: str = "user",
    machine_id: Optional[str] = None,
) -> Tuple[bool, str, str]:
    username = username.strip()
    role = (role or "user").strip().lower()
    if role not in _ALLOWED_ROLES:
        return False, "Invalid role.", role
    if not username or not password:
        return False, "Username and password are required.", role

    with _connect() as conn:
        existing = _get_user_by_username(conn, username)
        if existing:
            return False, "Username already exists.", role
        if role == "owner":
            owner = conn.execute(
                "SELECT id FROM users WHERE role = 'owner' LIMIT 1"
            ).fetchone()
            if owner:
                return False, "Owner account already exists.", role
            if not machine_id:
                machine_id = get_machine_id()
        password_hash = _hash_password(password)
        conn.execute(
            """
            INSERT INTO users (username, password_hash, role, created_at, machine_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (username, password_hash, role, _utc_now(), machine_id),
        )
        conn.commit()
    return True, "Account created.", role


def authenticate(
    username: str,
    password: str,
    machine_id: Optional[str] = None,
) -> Tuple[bool, str, str]:
    username = username.strip()
    if not username or not password:
        return False, "Username and password are required.", "user"

    with _connect() as conn:
        row = _get_user_by_username(conn, username)
        if not row:
            return False, "Invalid username or password.", "user"
        stored = row["password_hash"]
        if not stored or not _verify_password(password, stored):
            return False, "Invalid username or password.", row["role"]
        if row["role"] == "owner":
            current_machine = machine_id or get_machine_id()
            if row["machine_id"] and row["machine_id"] != current_machine:
                return False, "Owner account is locked to this machine.", "owner"
            if not row["machine_id"]:
                conn.execute(
                    "UPDATE users SET machine_id = ? WHERE id = ?",
                    (current_machine, row["id"]),
                )
                conn.commit()
        return True, "Login successful.", row["role"]


def log_session(user_id: int, module: str, success: int = 1) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO sessions (user_id, module, login_time, logout_time, success)
            VALUES (?, ?, ?, NULL, ?)
            """,
            (user_id, module, _utc_now(), int(bool(success))),
        )
        conn.commit()


def log_activity(user_id: int, action: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO activity (user_id, action, timestamp) VALUES (?, ?, ?)",
            (user_id, action, _utc_now()),
        )
        conn.commit()


def log_security(user_id: Optional[int], event: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO security (user_id, event, timestamp) VALUES (?, ?, ?)",
            (user_id, event, _utc_now()),
        )
        conn.commit()


def owner_exists_locked() -> bool:
    return owner_exists()


def create_owner(username: str, password: str) -> Tuple[bool, str]:
    ok, message, _role = register_user(
        username=username, password=password, role="owner", machine_id=get_machine_id()
    )
    return ok, "Owner account created." if ok else message


def verify_owner_login(username: str, password: str) -> Tuple[bool, str]:
    ok, message, _role = authenticate(username, password, machine_id=get_machine_id())
    return ok, message


def get_user_id(username: str) -> Optional[int]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        return row["id"] if row else None


def list_users() -> list[Dict[str, str]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, username, role, created_at, machine_id FROM users ORDER BY username"
        ).fetchall()
        return [
            {
                "id": row["id"],
                "username": row["username"],
                "role": row["role"],
                "created_at": row["created_at"],
                "machine_id": row["machine_id"],
            }
            for row in rows
        ]


def module_results_path(module_name: str, filename: Optional[str] = None) -> str:
    _ensure_storage()
    safe = "".join(ch for ch in module_name if ch.isalnum() or ch in ("-", "_")) or "module"
    if filename:
        name = filename
    else:
        name = f"{safe}.log"
    return os.path.join(_MODULES_RESULTS_DIR, name)


def log_module_result(module_name: str, content: str, filename: Optional[str] = None) -> str:
    path = module_results_path(module_name, filename)
    with open(path, "a", encoding="utf-8") as f:
        f.write(content.rstrip("\n") + "\n")
    return path


__all__ = [
    "SessionUser",
    "authenticate",
    "clear_session",
    "create_owner",
    "get_current_user",
    "get_machine_fingerprint",
    "get_machine_id",
    "get_owner_record",
    "get_owner_username",
    "get_user_id",
    "log_activity",
    "log_module_result",
    "log_security",
    "log_session",
    "list_users",
    "module_results_path",
    "owner_exists",
    "owner_exists_locked",
    "register_user",
    "set_current_user",
    "verify_owner_login",
]
