from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Dict, Optional

from colorama import Fore, Style

from blackhaven.auth_pkg.logger import log_action
from blackhaven.auth_pkg.session import get_current_user
from blackhaven.ui import render_layout


_SKILL_SCRIPT = "/home/hacker/.codex/skills/blackhaven-intel-core/scripts/osint_core.py"


def _prompt(prompt: str) -> str:
    sys.__stdout__.write(f"{Fore.GREEN}{prompt}{Style.RESET_ALL}")
    sys.__stdout__.flush()
    return input().strip()


def _run_script(target_type: str, target: str) -> Dict[str, object]:
    if not os.path.isfile(_SKILL_SCRIPT):
        return {"error": "Intel Core script not found."}
    python = sys.executable or "/usr/bin/python3"
    try:
        proc = subprocess.run(
            [python, _SKILL_SCRIPT, "--type", target_type, "--target", target, "--mode", "FULL_GOD_MODE"],
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
        )
        if proc.returncode != 0:
            return {"error": proc.stderr.strip() or "Intel Core failed."}
        return json.loads(proc.stdout)
    except Exception as exc:
        return {"error": str(exc)}


def run() -> None:
    user = get_current_user()
    if user:
        log_action(user.username, "intel core")

    while True:
        print(render_layout("BlackHaven Intel Core\nType 'exit' to return."), end="")
        target_type = _prompt("Target type (username/email/domain/ip): ").lower()
        if target_type in {"exit", "quit"}:
            return
        target = _prompt("Target: ")
        if target.lower() in {"exit", "quit"}:
            return

        result = _run_script(target_type, target)
        output = json.dumps(result, indent=2)
        print(render_layout(output), end="")
        _prompt("Press Enter to continue...")


def get_module():
    return {
        "name": "Intel Core",
        "description": "Passive OSINT intelligence engine",
        "run": run,
    }
