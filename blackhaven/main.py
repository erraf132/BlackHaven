#!/usr/bin/env python3
"""
BlackHaven Framework
Copyright (c) 2026 erraf132 and Vyrn.exe Official
All rights reserved.
"""

from .ui import display_logo, require_login, run_app
from .ui.banner import show_banner
from .utils.results_file import prompt_results_file

LEGAL_NOTICE = """============================================================
BLACKHAVEN FRAMEWORK — AUTHORIZED USE ONLY
==========================================

Copyright (c) 2026 erraf132 and Vyrn.exe Official
BlackHaven Framework
All rights reserved.

This software is provided for educational purposes and authorized
cybersecurity research only.

Any unauthorized use of this software against systems without
explicit permission is strictly prohibited and may violate laws.

The authors, erraf132 and Vyrn.exe Official, assume no liability and
are not responsible for any misuse, damage, or legal consequences.

By continuing, you accept full responsibility for your actions.

Type "I AGREE" to continue or press Ctrl+C to exit.

============================================================
"""


def show_legal_disclaimer() -> None:
    print(LEGAL_NOTICE)
    while True:
        try:
            user_input = input("> ").strip()
        except KeyboardInterrupt:
            print("\nExiting BlackHaven.")
            raise SystemExit(0)

        if user_input.casefold() == "i agree":
            return

        print('Confirmation not received. Type "I AGREE" to continue or Ctrl+C to exit.')


def main() -> int:
    show_legal_disclaimer()

    # Prompt for the shared results file before any auth flow.
    prompt_results_file()

    if not require_login():
        return 0

    show_banner()
    display_logo()

    return run_app()


if __name__ == "__main__":
    raise SystemExit(main())

