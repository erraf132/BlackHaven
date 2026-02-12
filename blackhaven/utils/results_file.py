"""
BlackHaven Framework
Copyright (c) 2026 erraf132 and Vyrn.exe Official
All rights reserved.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Optional

from blackhaven.auth_pkg.db import get_meta, set_meta, get_owner_record
from blackhaven.auth_pkg.session import get_current_user
from blackhaven.modules._utils import ensure_results_dir


_RESULTS_FILE_KEY = "results_file_path"


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_results_file() -> Optional[str]:
    return get_meta(_RESULTS_FILE_KEY)


def set_results_file(path: str) -> None:
    set_meta(_RESULTS_FILE_KEY, path)


def ensure_results_file(path: str) -> str:
    ensure_results_dir()
    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8"):
        pass
    return path


def prompt_results_file() -> str:
    """Prompt for results file path and store it for later writes."""
    default_path = os.path.join(
        os.path.expanduser("~"),
        ".blackhaven",
        "results",
        "blackhaven_results.jsonl",
    )
    while True:
        raw = input(f"Results file path [{default_path}]: ").strip()
        chosen = raw or default_path
        try:
            path = ensure_results_file(chosen)
        except OSError as exc:
            print(f"Unable to use results file: {exc}")
            continue
        if os.path.exists(path) and os.path.getsize(path) > 0:
            confirm = input("File exists. Append results? [y/N]: ").strip().lower()
            if confirm not in {"y", "yes"}:
                continue
        set_results_file(path)
        print(f"Results will be appended to: {path}")
        return path


def append_result_record(
    module_name: str,
    content: str,
    status: str = "success",
) -> Optional[str]:
    """
    Append a JSONL record to the selected results file.
    Includes timestamp, owner info, and current user context.
    """
    path = get_results_file()
    if not path:
        return None
    owner = get_owner_record() or {}
    user = get_current_user()
    record = {
        "timestamp": _utc_stamp(),
        "module": module_name,
        "status": status,
        "result": content,
        "owner": {
            "username": owner.get("username"),
            "id": owner.get("id"),
        },
        "user": {
            "username": user.username if user else None,
            "role": user.role if user else None,
        },
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return path
