"""
BlackHaven Framework
Copyright (c) 2026 erraf132 and Vyrn.exe Official
All rights reserved.
"""



from __future__ import annotations

import os
from datetime import datetime


def _activity_log_path() -> str:
    base_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    return os.path.abspath(os.path.join(base_dir, "activity.log"))


def log_action(username: str, action: str) -> None:
    path = _activity_log_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{username}] {action}\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)


def read_activity_log(limit: int | None = None) -> str:
    path = _activity_log_path()
    if not os.path.isfile(path):
        return "No activity logs found."
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    if limit:
        lines = lines[-limit:]
    return "".join(lines).strip() or "No activity logs found."
