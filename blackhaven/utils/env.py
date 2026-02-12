"""
BlackHaven Framework
Copyright (c) 2026 erraf132 and Vyrn.exe Official
All rights reserved.
"""



from __future__ import annotations

import os
from typing import Dict


def load_dotenv(path: str = ".env") -> Dict[str, str]:
    """Load environment variables from a .env file (simple KEY=VALUE parser)."""
    values: Dict[str, str] = {}
    if not os.path.isfile(path):
        return values
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"").strip("'")
            values[key] = value
            os.environ.setdefault(key, value)
    return values
