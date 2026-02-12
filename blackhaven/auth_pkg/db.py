"""
BlackHaven Framework
Copyright (c) 2026 erraf132 and Vyrn.exe Official
All rights reserved.
"""



from __future__ import annotations

import hashlib
import json
import os
import platform
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

import bcrypt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Base paths
_BASE_DIR = os.path.expanduser("~/.blackhaven")
_DB_PATH = os.path.join(_BASE_DIR, "blackhaven.db")
_MODULES_RESULTS_DIR = os.path.join(_BASE_DIR, "modules_results")
_LOGS_DIR = os.path.join(_BASE_DIR, "logs")

# Password hasher (Argon2id by default)
_PH = PasswordHasher()

# Roles allowed
_ALLOWED_ROLES = {"owner", "admin", "user"}


@dataclass
class SessionUser:
    """Simple in-memory session representation."""

    username: str
    role: str
    user_id: Optional[int] = None


_current_user: Optional[SessionUser] = None


def _utc_now() -> str:
    """Return current UTC timestamp in ISO-like format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _ensure_storage() -> None:
    """Ensure required directories exist with restrictive permissions."""
    os.makedirs(_BASE_DIR, mode=0o700, exist_ok=True)
    os.makedirs(_MODULES_RESULTS_DIR, mode=0o700, exist_ok=True)
    os.makedirs(_LOGS_DIR, mode=0o700, exist_ok=True)
    try:
        os.chmod(_BASE_DIR, 0o700)
    except OSError:
        pass


def _connect() -> sqlite3.Connection:
    """Open a SQLite connection with row factory and foreign keys enabled."""
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
    """Create required tables and indexes if missing."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('owner', 'admin', 'user')),
                created_at TEXT NOT NULL,
                machine_id TEXT,
                last_login TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                module_name TEXT NOT NULL,
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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        # Single-owner constraint (partial index)
        try:
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_single_owner "
                "ON users(role) WHERE role = 'owner'"
            )
        except sqlite3.OperationalError:
            # Older SQLite versions may not support partial indexes
            pass
        # Indexes for fast queries
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_module_name ON sessions(module_name)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_activity_user_id ON activity(user_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_security_user_id ON security(user_id)"
        )
        conn.commit()
        _migrate_legacy_users(conn)


def _get_meta(conn: sqlite3.Connection, key: str) -> Optional[str]:
    row = conn.execute(
        "SELECT value FROM meta WHERE key = ?",
        (key,),
    ).fetchone()
    return row["value"] if row else None


def get_meta(key: str) -> Optional[str]:
    """Return a metadata value by key."""
    initialize_database()
    with _connect() as conn:
        return _get_meta(conn, key)


def set_meta(key: str, value: str) -> None:
    """Set a metadata value by key."""
    initialize_database()
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
            (key, value),
        )
        conn.commit()


def get_or_create_install_id() -> str:
    """Return a stable install identifier for this machine."""
    initialize_database()
    with _connect() as conn:
        existing = _get_meta(conn, "install_id")
        if existing:
            return existing
        install_id = str(uuid.uuid4())
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES ('install_id', ?)",
            (install_id,),
        )
        conn.commit()
        return install_id


def _hash_password(password: str) -> str:
    """Hash a password using Argon2id."""
    return _PH.hash(password)


def _verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against a stored hash (Argon2id, bcrypt, or legacy sha256)."""
    if stored_hash.startswith("$argon2"):
        try:
            return _PH.verify(stored_hash, password)
        except VerifyMismatchError:
            return False
    if stored_hash.startswith("$2a$") or stored_hash.startswith("$2b$") or stored_hash.startswith("$2y$"):
        return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
    if stored_hash.startswith("sha256$"):
        return _verify_sha256(password, stored_hash)
    try:
        return _PH.verify(stored_hash, password)
    except VerifyMismatchError:
        return False


def _verify_sha256(password: str, stored_hash: str) -> bool:
    try:
        algo, salt, digest = stored_hash.split("$", 2)
    except ValueError:
        return False
    if algo != "sha256":
        return False
    computed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return computed == digest


def get_machine_id() -> str:
    """Derive a stable-ish machine id for owner binding."""
    raw = (
        platform.node()
        + platform.system()
        + platform.release()
        + platform.machine()
        + platform.processor()
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def set_current_user(username: str, role: str, user_id: Optional[int] = None) -> None:
    """Set in-memory session user."""
    global _current_user
    _current_user = SessionUser(username=username, role=role, user_id=user_id)


def get_current_user() -> Optional[SessionUser]:
    """Get in-memory session user."""
    return _current_user


def clear_session() -> None:
    """Clear in-memory session user."""
    global _current_user
    _current_user = None


def _get_user_row(conn: sqlite3.Connection, username: str) -> Optional[sqlite3.Row]:
    return conn.execute(
        """
        SELECT id, username, password_hash, role, machine_id, created_at, last_login
        FROM users WHERE username = ?
        """,
        (username,),
    ).fetchone()


def get_user_by_username(username: str) -> Optional[Dict[str, str]]:
    """Return a user record by username, or None."""
    initialize_database()
    with _connect() as conn:
        row = _get_user_row(conn, username)
        if not row:
            return None
        return {
            "id": row["id"],
            "username": row["username"],
            "role": row["role"],
            "created_at": row["created_at"],
            "machine_id": row["machine_id"],
            "last_login": row["last_login"],
        }


def get_owner_username() -> Optional[str]:
    """Return the owner's username if present."""
    initialize_database()
    with _connect() as conn:
        row = conn.execute(
            "SELECT username FROM users WHERE role = 'owner' LIMIT 1"
        ).fetchone()
        return row["username"] if row else None


def owner_exists() -> bool:
    """Return True if an owner exists."""
    initialize_database()
    with _connect() as conn:
        row = conn.execute(
            "SELECT id FROM users WHERE role = 'owner' LIMIT 1"
        ).fetchone()
        return row is not None


def get_owner_record() -> Optional[Dict[str, str]]:
    """Return owner info if present."""
    initialize_database()
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT id, username, role, created_at, machine_id, last_login
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
            "last_login": row["last_login"],
        }


def register_user(
    username: str,
    password: str,
    role: str = "user",
    machine_id: Optional[str] = None,
) -> Tuple[bool, str, str]:
    """
    Register a user and store a hashed password.
    Enforces single-owner and unique usernames.
    """
    initialize_database()
    username = username.strip()
    role = (role or "user").strip().lower()
    if not username or not password:
        return False, "Username and password are required.", role
    if role not in _ALLOWED_ROLES:
        return False, "Invalid role.", role

    with _connect() as conn:
        existing = _get_user_row(conn, username)
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
            INSERT INTO users (username, password_hash, role, created_at, machine_id, last_login)
            VALUES (?, ?, ?, ?, ?, NULL)
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
    """Authenticate user and return (ok, message, role)."""
    initialize_database()
    username = username.strip()
    if not username or not password:
        return False, "Username and password are required.", "user"

    with _connect() as conn:
        row = _get_user_row(conn, username)
        if not row:
            return False, "Invalid username or password.", "user"
        stored_hash = row["password_hash"]
        if not _verify_password(password, stored_hash):
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
        if stored_hash.startswith("$argon2") and _PH.check_needs_rehash(stored_hash):
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (_hash_password(password), row["id"]),
            )
        elif not stored_hash.startswith("$argon2"):
            # Upgrade legacy hashes (bcrypt/sha256) after successful login
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (_hash_password(password), row["id"]),
            )
        conn.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (_utc_now(), row["id"]),
        )
        conn.commit()
        return True, "Login successful.", row["role"]


def log_session(user_id: int, module_name: str, success: bool = True) -> None:
    """Log a session entry for a user."""
    initialize_database()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO sessions (user_id, module_name, login_time, logout_time, success)
            VALUES (?, ?, ?, NULL, ?)
            """,
            (user_id, module_name, _utc_now(), int(bool(success))),
        )
        conn.commit()


def read_session_log(limit: Optional[int] = None) -> str:
    """Return a formatted session log string."""
    initialize_database()
    with _connect() as conn:
        query = (
            """
            SELECT s.login_time, u.username, s.module_name
            FROM sessions s
            JOIN users u ON u.id = s.user_id
            ORDER BY s.login_time DESC
            """
        )
        params: tuple = ()
        if limit:
            query += " LIMIT ?"
            params = (int(limit),)
        rows = conn.execute(query, params).fetchall()
    if not rows:
        return "No session logs found."
    lines = [f"[{row['login_time']}] {row['username']} | {row['module_name']}" for row in rows]
    return "\n".join(lines)


def log_activity(user_id: int, action: str) -> None:
    """Log a user activity event."""
    initialize_database()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO activity (user_id, action, timestamp) VALUES (?, ?, ?)",
            (user_id, action, _utc_now()),
        )
        conn.commit()


def log_security(user_id: Optional[int], event: str) -> None:
    """Log a security event."""
    initialize_database()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO security (user_id, event, timestamp) VALUES (?, ?, ?)",
            (user_id, event, _utc_now()),
        )
        conn.commit()


def module_results_path(module_name: str, filename: Optional[str] = None) -> str:
    """Return a safe results file path for a module."""
    _ensure_storage()
    safe = "".join(ch for ch in module_name if ch.isalnum() or ch in ("-", "_")) or "module"
    name = filename or f"{safe}.log"
    return os.path.join(_MODULES_RESULTS_DIR, name)


def log_module_result(module_name: str, content: str, filename: Optional[str] = None) -> str:
    """Append module output to a result file and return its path."""
    path = module_results_path(module_name, filename)
    with open(path, "a", encoding="utf-8") as f:
        f.write(content.rstrip("\n") + "\n")
    return path


def get_user_id(username: str) -> Optional[int]:
    """Return a user id for a given username."""
    initialize_database()
    with _connect() as conn:
        row = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        return row["id"] if row else None


def list_users() -> list[Dict[str, str]]:
    """List all users."""
    initialize_database()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, username, role, created_at, machine_id, last_login FROM users ORDER BY username"
        ).fetchall()
        return [
            {
                "id": row["id"],
                "username": row["username"],
                "role": row["role"],
                "created_at": row["created_at"],
                "machine_id": row["machine_id"],
                "last_login": row["last_login"],
            }
            for row in rows
        ]


def create_owner(username: str, password: str, machine_id: Optional[str] = None) -> Tuple[bool, str]:
    """Create an owner account (single-owner restriction enforced)."""
    ok, message, _role = register_user(
        username=username,
        password=password,
        role="owner",
        machine_id=machine_id or get_machine_id(),
    )
    return ok, "Owner account created." if ok else message


def verify_owner_login(username: str, password: str, machine_id: Optional[str] = None) -> Tuple[bool, str]:
    """Authenticate owner with machine binding."""
    ok, message, _role = authenticate(
        username=username, password=password, machine_id=machine_id or get_machine_id()
    )
    return ok, message


def _legacy_paths() -> list[str]:
    """Return known legacy user store paths."""
    here = os.path.dirname(__file__)
    auth_users = os.path.abspath(os.path.join(here, "..", "data", "users.json"))
    security_users = os.path.abspath(os.path.join(here, "..", "..", "security", "users.json"))
    return [auth_users, security_users]


def _load_legacy_users() -> list[Dict[str, str]]:
    """Load users from legacy JSON stores."""
    users: list[Dict[str, str]] = []
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
                if not isinstance(entry, dict):
                    continue
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
            INSERT INTO users (username, password_hash, role, created_at, machine_id, last_login)
            VALUES (?, ?, ?, ?, NULL, NULL)
            """,
            (username, password_hash, role, created_at),
        )
    conn.execute(
        "INSERT OR REPLACE INTO meta (key, value) VALUES ('legacy_users_migrated', '1')"
    )
    conn.commit()


__all__ = [
    "SessionUser",
    "authenticate",
    "create_owner",
    "clear_session",
    "get_current_user",
    "get_owner_record",
    "get_owner_username",
    "get_meta",
    "get_or_create_install_id",
    "get_user_id",
    "get_user_by_username",
    "initialize_database",
    "list_users",
    "log_activity",
    "log_module_result",
    "log_security",
    "log_session",
    "read_session_log",
    "get_machine_id",
    "module_results_path",
    "owner_exists",
    "register_user",
    "set_meta",
    "set_current_user",
    "verify_owner_login",
]
