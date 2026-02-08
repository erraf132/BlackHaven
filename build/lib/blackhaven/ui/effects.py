from __future__ import annotations

import shutil
import sys
import time
from typing import Dict, Iterable, Tuple

from colorama import Fore, Style

from .elite_render import load_logo_lines


_LOGO_CACHE: Dict[str, object] = {
    "rendered": False,
    "height": 0,
    "width": 0,
    "lines": (),
}


def typing_effect(text: str, speed: float = 0.002) -> None:
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(speed)


def persistent_logo(lines: Iterable[str] | None = None) -> Tuple[str, int]:
    if lines is None:
        lines = load_logo_lines()
    lines = tuple(lines)
    width = shutil.get_terminal_size((80, 24)).columns
    rendered_lines = []
    for line in lines:
        padding = max(0, (width - len(line)) // 2)
        rendered_lines.append(
            f"{' ' * padding}{Fore.RED}{Style.BRIGHT}{line}{Style.RESET_ALL}"
        )
    logo = "\n".join(rendered_lines)
    if (
        not _LOGO_CACHE["rendered"]
        or _LOGO_CACHE["lines"] != lines
        or _LOGO_CACHE["width"] != width
    ):
        _LOGO_CACHE["rendered"] = True
        _LOGO_CACHE["height"] = len(lines)
        _LOGO_CACHE["width"] = width
        _LOGO_CACHE["lines"] = lines
        return f"\x1b[2J\x1b[H{logo}{Style.RESET_ALL}", len(lines)
    return "", int(_LOGO_CACHE["height"])
