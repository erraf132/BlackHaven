"""
BlackHaven Framework
Copyright (c) 2026 erraf132 and Vyrn.exe Official
All rights reserved.
"""



from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import bcrypt

_BASE_DIR = os.path.expanduser("~/.blackhaven")
_DB_DIR = os.path.join(_BASE_DIR, "database")
_DB_PATH = os.path.join(_DB_DIR, "blackhaven.db")

_ALLOWED_ROLES = {"owner", "admin", "user"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _ensure_storage() -> None:
    os.makedirs(_DB_DIR, mode=0o700, exist_ok=True)
    try:
        os.chmod(_DB_DIR, 0o700)
    except OSError:
        pass


def _connect() -> sqlite3.Connection:
    _ensure_storage()
    created = not os.path.exists(_DB_PATH)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    if created:
        try:
            os.chmod(_DB_PATH, 0o600)
        except OSError:
            pass
    return conn


def initialize_database() -> None:
    """Create all tables and indexes if missing."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('owner', 'admin', 'user')),
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                module_run TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                success INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS modules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                last_run TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_module_run ON sessions(module_run)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_logs_user_id ON logs(user_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_modules_name ON modules(name)"
        )
        conn.commit()
        _migrate_legacy_users(conn)


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, stored_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))


def add_user(username: str, password: str, role: str) -> Tuple[bool, str]:
    """Add a new user with a hashed password."""
    initialize_database()
    username = username.strip()
    role = role.strip().lower()
    if not username or not password:
        return False, "Username and password are required."
    if role not in _ALLOWED_ROLES:
        return False, "Invalid role."

    with _connect() as conn:
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if existing:
            return False, "Username already exists."
        conn.execute(
            """
            INSERT INTO users (username, password_hash, role, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (username, _hash_password(password), role, _utc_now()),
        )
        conn.commit()
    return True, "User added."


def authenticate_user(username: str, password: str) -> Tuple[bool, str]:
    """Authenticate a user by username and password."""
    initialize_database()
    username = username.strip()
    if not username or not password:
        return False, "Username and password are required."

    with _connect() as conn:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if not row:
            return False, "Invalid username or password."
        if _verify_password(password, row["password_hash"]):
            return True, "Login successful."
    return False, "Invalid username or password."


def log_session(user_id: int, module_name: str, success: bool) -> None:
    """Record a module session for a user."""
    initialize_database()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO sessions (user_id, module_run, timestamp, success)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, module_name, _utc_now(), int(bool(success))),
        )
        conn.commit()


def log_action(user_id: Optional[int], action: str) -> None:
    """Log an action event. user_id can be None."""
    initialize_database()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO logs (user_id, action, timestamp) VALUES (?, ?, ?)",
            (user_id, action, _utc_now()),
        )
        conn.commit()


def get_users() -> List[Dict[str, str]]:
    initialize_database()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, username, role, created_at FROM users ORDER BY username"
        ).fetchall()
        return [
            {
                "id": row["id"],
                "username": row["username"],
                "role": row["role"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]


def get_sessions() -> List[Dict[str, str]]:
    initialize_database()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, user_id, module_run, timestamp, success
            FROM sessions ORDER BY timestamp DESC
            """
        ).fetchall()
        return [
            {
                "id": row["id"],
                "user_id": row["user_id"],
                "module_run": row["module_run"],
                "timestamp": row["timestamp"],
                "success": bool(row["success"]),
            }
            for row in rows
        ]


def get_logs() -> List[Dict[str, str]]:
    initialize_database()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, user_id, action, timestamp FROM logs ORDER BY timestamp DESC"
        ).fetchall()
        return [
            {
                "id": row["id"],
                "user_id": row["user_id"],
                "action": row["action"],
                "timestamp": row["timestamp"],
            }
            for row in rows
        ]


def get_modules() -> List[Dict[str, str]]:
    initialize_database()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, name, description, last_run, created_at
            FROM modules ORDER BY name
            """
        ).fetchall()
        return [
            {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "last_run": row["last_run"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]


def _legacy_paths() -> List[str]:
    here = os.path.dirname(__file__)
    auth_users = os.path.abspath(os.path.join(here, "..", "..", "auth_pkg", "data", "users.json"))
    security_users = os.path.abspath(os.path.join(here, "..", "..", "security", "users.json"))
    return [auth_users, security_users]


def _load_legacy_users() -> List[Dict[str, str]]:
    users: List[Dict[str, str]] = []
    for path in _legacy_paths():
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        if isinstance(data, dict) and "users" in data and isinstance(data["users"], list):
            for entry in data["users"]:
                if isinstance(entry, dict):
                    users.append(entry)
            continue
        if isinstance(data, dict):
            for username, info in data.items():
                if not isinstance(info, dict):
                    continue
                users.append(
                    {
                        "username": username,
                        "password_hash": info.get("password_hash", ""),
                        "role": info.get("role", "user"),
                        "created_at": info.get("created", "") or info.get("created_at", ""),
                    }
                )
    return users


def _migrate_legacy_users(conn: sqlite3.Connection) -> None:
    """One-time migration from legacy JSON user stores into SQLite."""
    row = conn.execute(
        "SELECT value FROM meta WHERE key = 'legacy_users_migrated'"
    ).fetchone()
    if row and row["value"] == "1":
        return
    users = _load_legacy_users()
    for entry in users:
        username = str(entry.get("username", "")).strip()
        if not username:
            continue
        role = str(entry.get("role", "user")).strip().lower()
        if role not in _ALLOWED_ROLES:
            role = "user"
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if existing:
            continue
        password_hash = str(entry.get("password_hash", "")).strip()
        if not password_hash:
            continue
        created_at = str(entry.get("created_at") or _utc_now())
        conn.execute(
            """
            INSERT INTO users (username, password_hash, role, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (username, password_hash, role, created_at),
        )
    conn.execute(
        "INSERT OR REPLACE INTO meta (key, value) VALUES ('legacy_users_migrated', '1')"
    )
    conn.commit()


__all__ = [
    "add_user",
    "authenticate_user",
    "get_logs",
    "get_modules",
    "get_sessions",
    "get_users",
    "initialize_database",
    "log_action",
    "log_session",
]
