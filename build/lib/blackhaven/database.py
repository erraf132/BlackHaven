from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from typing import Dict, Optional, Tuple

import bcrypt


_DB_DIR = os.path.expanduser("~/.blackhaven")
_DB_PATH = os.path.join(_DB_DIR, "admin.db")


def _ensure_dir() -> None:
    os.makedirs(_DB_DIR, mode=0o700, exist_ok=True)
    try:
        os.chmod(_DB_DIR, 0o700)
    except OSError:
        pass


def _connect() -> sqlite3.Connection:
    _ensure_dir()
    created = not os.path.exists(_DB_PATH)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    _init_db(conn)
    _migrate_admin_owner(conn)
    _ensure_owner_lock(conn)
    if created:
        try:
            os.chmod(_DB_PATH, 0o600)
        except OSError:
            pass
    return conn


def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS owner (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            owner_public_key TEXT,
            hostname TEXT NOT NULL,
            machine_id TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS owner_lock (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TRIGGER IF NOT EXISTS owner_lock_no_delete
        BEFORE DELETE ON owner_lock
        BEGIN
            SELECT RAISE(ABORT, 'owner lock is permanent');
        END;
        """
    )
    conn.execute(
        """
        CREATE TRIGGER IF NOT EXISTS owner_no_delete
        BEFORE DELETE ON owner
        BEGIN
            SELECT RAISE(ABORT, 'owner record is permanent');
        END;
        """
    )
    conn.execute(
        """
        CREATE TRIGGER IF NOT EXISTS owner_insert_guard
        BEFORE INSERT ON owner
        WHEN EXISTS (SELECT 1 FROM owner_lock WHERE id = 1)
        BEGIN
            SELECT RAISE(ABORT, 'owner creation is locked');
        END;
        """
    )
    conn.commit()


def _ensure_owner_lock(conn: sqlite3.Connection) -> None:
    row = conn.execute("SELECT id FROM owner_lock WHERE id = 1").fetchone()
    if row:
        return
    owner = conn.execute("SELECT id FROM owner WHERE id = 1").fetchone()
    if owner:
        conn.execute(
            "INSERT INTO owner_lock (id, created_at) VALUES (1, ?)",
            (datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),),
        )
        conn.commit()


def _migrate_admin_owner(conn: sqlite3.Connection) -> None:
    owner = conn.execute("SELECT id FROM owner WHERE id = 1").fetchone()
    if owner:
        return
    admin_table = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='admin'"
    ).fetchone()
    if not admin_table:
        return
    admin = conn.execute(
        "SELECT username, password_hash, created_at FROM admin WHERE id = 1"
    ).fetchone()
    if not admin:
        return
    fingerprint = get_machine_fingerprint()
    conn.execute(
        """
        INSERT INTO owner (
            id, username, password_hash, created_at, owner_public_key, hostname, machine_id
        ) VALUES (1, ?, ?, ?, ?, ?, ?)
        """,
        (
            admin["username"],
            admin["password_hash"],
            admin["created_at"],
            None,
            fingerprint["hostname"],
            fingerprint["machine_id"],
        ),
    )
    conn.execute(
        "INSERT INTO owner_lock (id, created_at) VALUES (1, ?)",
        (datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),),
    )
    conn.commit()


def _read_machine_id() -> str:
    candidates = [
        "/etc/machine-id",
        "/var/lib/dbus/machine-id",
    ]
    for path in candidates:
        try:
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    return f.read().strip()
        except Exception:
            continue
    return "unknown"


def get_machine_fingerprint() -> Dict[str, str]:
    import platform

    return {
        "hostname": platform.node(),
        "machine_id": _read_machine_id(),
    }
    conn.commit()


def owner_exists() -> bool:
    with _connect() as conn:
        row = conn.execute("SELECT username FROM owner WHERE id = 1").fetchone()
        return row is not None


def owner_lock_exists() -> bool:
    with _connect() as conn:
        row = conn.execute("SELECT id FROM owner_lock WHERE id = 1").fetchone()
        return row is not None


def get_owner_username() -> Optional[str]:
    with _connect() as conn:
        row = conn.execute("SELECT username FROM owner WHERE id = 1").fetchone()
        return row["username"] if row else None


def get_owner_record() -> Optional[Dict[str, str]]:
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT username, created_at, owner_public_key, hostname, machine_id
            FROM owner WHERE id = 1
            """
        ).fetchone()
        if not row:
            return None
        return {
            "username": row["username"],
            "created_at": row["created_at"],
            "owner_public_key": row["owner_public_key"],
            "hostname": row["hostname"],
            "machine_id": row["machine_id"],
        }


def create_owner(username: str, password: str, owner_public_key: Optional[str] = None) -> Tuple[bool, str]:
    username = username.strip()
    if not username or not password:
        return False, "Username and password are required."

    with _connect() as conn:
        lock = conn.execute("SELECT id FROM owner_lock WHERE id = 1").fetchone()
        if lock:
            return False, "Owner creation is locked."
        existing = conn.execute("SELECT username FROM owner WHERE id = 1").fetchone()
        if existing:
            return False, "Owner account already exists."

        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        fingerprint = get_machine_fingerprint()
        conn.execute(
            """
            INSERT INTO owner (
                id, username, password_hash, created_at, owner_public_key, hostname, machine_id
            ) VALUES (1, ?, ?, ?, ?, ?, ?)
            """,
            (
                username,
                password_hash,
                datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                owner_public_key,
                fingerprint["hostname"],
                fingerprint["machine_id"],
            ),
        )
        conn.execute(
            "INSERT INTO owner_lock (id, created_at) VALUES (1, ?)",
            (datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),),
        )
        conn.commit()

    return True, "Owner account created."


def verify_owner_login(username: str, password: str) -> Tuple[bool, str]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT username, password_hash, hostname, machine_id FROM owner WHERE id = 1"
        ).fetchone()
        if not row:
            return False, "Owner account not found."
        if row["username"].lower() != username.lower():
            return False, "Invalid username or password."
        fingerprint = get_machine_fingerprint()
        if row["hostname"] != fingerprint["hostname"] or row["machine_id"] != fingerprint["machine_id"]:
            return False, "Owner account is locked to another machine."
        stored = row["password_hash"]
        if bcrypt.checkpw(password.encode("utf-8"), stored.encode("utf-8")):
            return True, "Login successful."
        return False, "Invalid username or password."
