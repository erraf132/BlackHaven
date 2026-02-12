from __future__ import annotations

import os
from typing import List


def _logo_path() -> str:
    return os.path.join(os.path.dirname(__file__), "logo.txt")


def load_logo_lines() -> List[str]:
    path = _logo_path()
    if not os.path.isfile(path):
        return ["BLACKHAVEN"]
    with open(path, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f.readlines()]
    return [line if line else "" for line in lines]
