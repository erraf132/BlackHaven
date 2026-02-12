"""
BlackHaven Framework
Copyright (c) 2026 erraf132 and Vyrn.exe Official
All rights reserved.
"""



from __future__ import annotations

import re

from colorama import Fore, Style

from blackhaven.auth_pkg.logger import log_action
from blackhaven.auth_pkg.session import get_current_user
from blackhaven.core.username_engine import search_username


def run() -> None:
    username = input("Username to search: ").strip()
    if not username:
        print("No username provided.")
        return
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,32}", username):
        print("Warning: username contains unusual characters; results may be unreliable.")

    user = get_current_user()
    if user:
        log_action(user.username, f"searched username {username}")

    print("\nChecking sites:")
    results = search_username(username)

    for entry in sorted(results, key=lambda x: x["site"].lower()):
        status = entry["status"]
        found = entry["found"]
        color = Fore.GREEN if found == "yes" else Fore.RED if found == "no" else Fore.YELLOW
        line = f"- {entry['site']}: {status} ({entry['url']})"
        print(f"{color}{line}{Style.RESET_ALL}")
    print("\nSaved results to: /home/hacker/BlackHaven/results/usernames/")


def get_module():
    return {
        "name": "Username Search",
        "description": "Check common sites for a username",
        "run": run,
    }
