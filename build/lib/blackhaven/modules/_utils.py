from __future__ import annotations

import csv
import json
import logging
import os
from datetime import datetime
from typing import Iterable, List

_BASE_DIR = os.path.join(os.path.expanduser("~"), ".blackhaven")
RESULTS_DIR = os.path.join(_BASE_DIR, "results")
PLUGINS_DIR = os.path.join(_BASE_DIR, "plugins")
LOG_PATH = os.path.join(RESULTS_DIR, "blackhaven.log")


def ensure_results_dir() -> None:
    os.makedirs(RESULTS_DIR, exist_ok=True)


def ensure_plugins_dir() -> None:
    os.makedirs(PLUGINS_DIR, exist_ok=True)


def user_plugins_dir() -> str:
    ensure_plugins_dir()
    return PLUGINS_DIR


def setup_logging() -> None:
    ensure_results_dir()
    if logging.getLogger().handlers:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.FileHandler(LOG_PATH, encoding="utf-8")],
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def save_result(module_name: str, lines: Iterable[str]) -> str:
    ensure_results_dir()
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(ch for ch in module_name if ch.isalnum() or ch in ("-", "_"))
    filename = f"{safe_name}_{stamp}.txt"
    path = os.path.join(RESULTS_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line.rstrip("\n") + "\n")
    return path


def save_json(module_name: str, data: object) -> str:
    ensure_results_dir()
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(ch for ch in module_name if ch.isalnum() or ch in ("-", "_"))
    filename = f"{safe_name}_{stamp}.json"
    path = os.path.join(RESULTS_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path


def save_csv(module_name: str, rows: Iterable[dict]) -> str:
    ensure_results_dir()
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(ch for ch in module_name if ch.isalnum() or ch in ("-", "_"))
    filename = f"{safe_name}_{stamp}.csv"
    path = os.path.join(RESULTS_DIR, filename)
    rows_list = list(rows)
    if not rows_list:
        with open(path, "w", encoding="utf-8") as f:
            f.write("")
        return path
    fieldnames = list(rows_list[0].keys())
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_list)
    return path


def prompt_export_formats() -> set[str]:
    prompt = "Export JSON/CSV? [j]son/[c]sv/[b]oth/[n]o: "
    choice = input(prompt).strip().lower()
    if choice == "j":
        return {"json"}
    if choice == "c":
        return {"csv"}
    if choice == "b":
        return {"json", "csv"}
    return set()


def export_results(module_name: str, lines: Iterable[str], rows: Iterable[dict] | None = None) -> List[str]:
    paths = [save_result(module_name, lines)]
    formats = prompt_export_formats() if rows is not None else set()
    if rows is not None:
        rows_list = list(rows)
        if "json" in formats:
            paths.append(save_json(module_name, rows_list))
        if "csv" in formats:
            paths.append(save_csv(module_name, rows_list))
    return paths
