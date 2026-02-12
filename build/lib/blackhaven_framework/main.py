#!/usr/bin/env python3
"""BlackHaven Framework entry point."""

from core.framework import BlackHavenFramework


def main() -> None:
    framework = BlackHavenFramework()
    framework.run()


if __name__ == "__main__":
    main()
