#!/usr/bin/env python3

from .ui import display_logo, require_login, run_app, show_disclaimer_screen


def main() -> int:
    if not show_disclaimer_screen():
        return 0
    if not require_login():
        return 0
    display_logo()
    return run_app()


if __name__ == "__main__":
    raise SystemExit(main())
