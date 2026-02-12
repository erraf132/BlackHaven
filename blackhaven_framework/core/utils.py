"""
BlackHaven Framework
Copyright (c) 2026 erraf132 and Vyrn.exe Official
All rights reserved.
"""


from __future__ import annotations
import json
import logging
import socket
import time
from dataclasses import dataclass
from typing import Any, Dict
from colorama import Fore, Style, init
import yaml
# Initialize color output once for the application.
init(autoreset=True)
@dataclass
class Timer:

    start_time: float = 0.0

    def __enter__(self) -> "Timer":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        pass

    @property
    def elapsed(self) -> float:
        return time.perf_counter() - self.start_time


class Output:
    """Colored console output helper."""

    @staticmethod
    def info(message: str) -> None:
        print(f"{Fore.CYAN}[i]{Style.RESET_ALL} {message}")

    @staticmethod
    def success(message: str) -> None:
        print(f"{Fore.GREEN}[+]{Style.RESET_ALL} {message}")

    @staticmethod
    def warning(message: str) -> None:
        print(f"{Fore.YELLOW}[!]{Style.RESET_ALL} {message}")

    @staticmethod
    def error(message: str) -> None:
        print(f"{Fore.RED}[-]{Style.RESET_ALL} {message}")

    @staticmethod
    def header(message: str) -> None:
        print(f"{Fore.MAGENTA}{message}{Style.RESET_ALL}")

    @staticmethod
    def progress(message: str) -> None:
        print(f"{Fore.BLUE}{message}{Style.RESET_ALL}", end="\r")


class JSONStore:
    """JSON export helper with consistent formatting."""

    @staticmethod
    def write(path: str, data: Dict[str, Any]) -> None:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)


def setup_logger(log_path: str) -> logging.Logger:
    """Configure and return a logger instance."""

    logger = logging.getLogger("blackhaven")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def safe_resolve(hostname: str) -> str | None:
    """Resolve hostname to IP safely, returning None on failure."""

    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return None


class ConfigManager:
    """Load and expose YAML configuration settings."""

    def __init__(self, path: str) -> None:
        self.path = path
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                return yaml.safe_load(handle) or {}
        except FileNotFoundError:
            return {}
        except Exception:
            return {}

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)
