from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Iterable, List

from blackhaven.modules._utils import ensure_results_dir


BASE_DIR = os.path.join(os.path.expanduser("~"), ".blackhaven")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
REPORTS_DIR = os.path.join(RESULTS_DIR, "reports")


def ensure_reports_dir() -> None:
    ensure_results_dir()
    os.makedirs(REPORTS_DIR, exist_ok=True)


def save_text(name: str, lines: Iterable[str]) -> str:
    ensure_results_dir()
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(ch for ch in name if ch.isalnum() or ch in ("-", "_"))
    path = os.path.join(RESULTS_DIR, f"{safe_name}_{stamp}.txt")
    with open(path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line.rstrip("\n") + "\n")
    return path


def save_json(name: str, data: object) -> str:
    ensure_results_dir()
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(ch for ch in name if ch.isalnum() or ch in ("-", "_"))
    path = os.path.join(RESULTS_DIR, f"{safe_name}_{stamp}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path


def save_report(name: str, content: str, ext: str) -> str:
    ensure_reports_dir()
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(ch for ch in name if ch.isalnum() or ch in ("-", "_"))
    filename = f"{safe_name}_{stamp}.{ext}"
    path = os.path.join(REPORTS_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def save_report_bundle(name: str, txt: str, md: str, json_text: str) -> List[str]:
    paths = [
        save_report(name, txt, "txt"),
        save_report(name, md, "md"),
        save_report(name, json_text, "json"),
    ]
    return paths
