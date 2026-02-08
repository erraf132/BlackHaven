#!/usr/bin/env python3

from blackhaven.auth import require_login
from .ui import run_app, show_disclaimer_screen


def main() -> int:
    if not show_disclaimer_screen():
        return 0
    require_login()
    return run_app()


if __name__ == "__main__":
    raise SystemExit(main())
