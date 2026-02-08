from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class SessionUser:
    username: str
    role: str


_current_user: Optional[SessionUser] = None


def set_current_user(username: str, role: str) -> None:
    global _current_user
    _current_user = SessionUser(username=username, role=role)


def get_current_user() -> Optional[SessionUser]:
    return _current_user


def clear_session() -> None:
    global _current_user
    _current_user = None
