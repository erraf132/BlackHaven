from __future__ import annotations

import sys
from datetime import datetime
from typing import List

from blackhaven.auth_pkg.logger import log_action
from blackhaven.auth_pkg.session import get_current_user
from blackhaven.ui import render_layout


def _respond(message: str) -> str:
    lowered = message.lower().strip()
    if any(token in lowered for token in ("hello", "hi", "hey")):
        return "Hello. I can help with quick OSINT notes or navigation tips."
    if "time" in lowered:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"Local time: {now}"
    if "help" in lowered:
        return "Try: hello, time, help, or type anything to echo. Type exit to leave."
    return f"Echo: {message[::-1]}"


def _render_screen(history: List[str]) -> None:
    content = "\n".join(history)
    sys.__stdout__.write(render_layout(content))
    sys.__stdout__.flush()


def run() -> None:
    user = get_current_user()
    if user:
        log_action(user.username, "ai assistant")

    history: List[str] = [
        "AI Assistant Ready",
        "Type 'help' for options. Type 'exit' or 'quit' to return.",
    ]

    while True:
        history.append("")
        history.append("You > ")
        _render_screen(history)
        message = input()
        if message is None:
            break
        lowered = message.strip().lower()
        if lowered in {"exit", "quit"}:
            break
        response = _respond(message)
        history[-1] = f"You > {message}"
        history.append(f"AI > {response}")


def get_module():
    return {
        "name": "AI Assistant",
        "description": "Interactive local assistant",
        "run": run,
    }
