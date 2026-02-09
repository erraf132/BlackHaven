"""
BlackHaven Framework

Example usage in main CLI:
from blackhaven.ui.banner import show_banner
show_banner()
"""


def show_banner() -> None:
    banner = r"""
        __
   ____/  \_____________________________________________________
  /                                                           \
 /   BLACKHAVEN                                                |
 \                                                           /
  \_________________________________________________________/~~~

coded by erraf132 and Vyrn.exe Official
Copyright (c) 2026
All rights reserved.
"""

    try:
        from rich.console import Console

        console = Console()
        console.print(banner, style="bold red")
    except ImportError:
        print(banner)
