from __future__ import annotations

import getpass
import importlib
import importlib.util
import io
import os
import pkgutil
import re
import shutil
import subprocess
import textwrap
from contextlib import redirect_stderr, redirect_stdout
from types import ModuleType
from typing import Dict, List, Optional

from colorama import Fore, Style, init

from blackhaven.auth import current_user_is_admin
from blackhaven.auth_pkg.auth import authenticate, ensure_owner, register_user
from blackhaven.auth_pkg.logger import log_action, read_activity_log
from blackhaven.auth_pkg.owner import owner_exists
from blackhaven.auth_pkg.session import get_current_user, set_current_user
from blackhaven.auth_pkg.db import get_owner_record, get_user_id
from blackhaven.security.auth import log_session, read_session_log
from blackhaven.modules._utils import get_logger, setup_logging, user_plugins_dir

LOG = get_logger("BlackHaven")

THEME_TEXT = Fore.GREEN
THEME_LOGO = Fore.RED + Style.BRIGHT
THEME_RESET = Style.RESET_ALL

_SECURITY_LOG_PATH = os.path.join(os.path.expanduser("~"), ".blackhaven", "results", "security.log")
_LOGO_LINES: Optional[List[str]] = [
    "             ____  _        _    ____ _  ___   _    ___     _______ _   _",
    "            | __ )| |      / \\  / ___| |/ / | | |  / \\ \\   / / ____| \\ | |",
    "            |  _ \\| |     / _ \\| |   | ' /| |_| | / _ \\ \\ / /|  _| |  \\| |",
    "            | |_) | |___ / ___ \\ |___| . \\|  _  |/ ___ \\ V / | |___| |\\  |",
    "            |____/|_____/_/   \\_\\____|_|\\_\\_| |_/_/   \\_\\_/  |_____|_| \\_|",
    "                                         BLACKHAVEN",
]
_VERSION_LINES: Optional[List[str]] = [
    "BlackHaven v3.0 OMEGA",
    "coded by Vyrn.exe",
]


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def _terminal_width() -> int:
    return max(80, shutil.get_terminal_size((80, 24)).columns)


def _center_line(text: str, width: int) -> str:
    visible_text = re.sub(r"\x1b\[[0-9;]*m", "", text)
    padding = max(0, (width - len(visible_text)) // 2)
    return " " * padding + text


def _load_logo() -> List[str]:
    global _LOGO_LINES
    return _LOGO_LINES


def display_logo() -> None:
    print(render_layout(), end="")
    return None


def _render_logo() -> str:
    width = _terminal_width()
    lines = _load_logo()

    logo = "\n".join(
        _center_line(f"{THEME_LOGO}{line}{THEME_RESET}", width)
        for line in lines
    )

    version = "\n".join(
        _center_line(f"{THEME_TEXT}{line}{THEME_RESET}", width)
        for line in _VERSION_LINES or []
    )

    if version:
        return logo + "\n\n" + version
    return logo


def render_layout(content: Optional[str] = None) -> str:
    logo_block = _render_logo()
    if content:
        content_block = f"{THEME_TEXT}{content}{THEME_RESET}"
        return f"\x1b[2J\x1b[H{logo_block}\n\n{content_block}\n"
    return f"\x1b[2J\x1b[H{logo_block}\n"


def render_layout_elite(content: Optional[str] = None) -> str:
    return render_layout(content)


def _prompt_text(text: str) -> str:
    return f"{THEME_TEXT}{text}{THEME_RESET}"


def _input(prompt: str = "") -> str:
    if prompt:
        return input(_prompt_text(prompt))
    return input()


def _getpass(prompt: str) -> str:
    return getpass.getpass(_prompt_text(prompt))


def _wrap_text(text: str, width: int) -> str:
    wrapped = []
    for line in text.splitlines():
        wrapped.extend(textwrap.wrap(line, width=width) or [""])
    return "\n".join(wrapped)


def _read_security_log(limit: int = 200) -> str:
    try:
        with open(_SECURITY_LOG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        return "No security logs found."
    if limit:
        lines = lines[-limit:]
    return "".join(lines).strip() or "No security logs found."


def show_disclaimer_screen() -> bool:
    init(autoreset=True)
    width = min(80, _terminal_width() - 4)
    title = "LEGAL DISCLAIMER AND AUTHORIZED USE ONLY"
    header = "[ SYSTEM NOTICE ]"
    body = (
        "This system is restricted to authorized users only. "
        "Unauthorized access is prohibited and may be prosecuted.\n\n"
        "All actions are monitored and logged.\n\n"
        "Type: I UNDERSTAND\n"
        "to acknowledge and continue.\n\n"
        "Type: EXIT to quit."
    )
    wrapped = _wrap_text(body, width - 6)

    top = "┌" + ("─" * (width - 2)) + "┐"
    bottom = "└" + ("─" * (width - 2)) + "┘"

    def build_panel(text_block: str) -> str:
        lines = [
            top,
            "│" + " " * (width - 2) + "│",
            "│" + _center_line(title, width - 2).ljust(width - 2) + "│",
            "│" + " " * (width - 2) + "│",
            "│" + _center_line(header, width - 2).ljust(width - 2) + "│",
            "│" + " " * (width - 2) + "│",
        ]
        for line in text_block.splitlines():
            lines.append("│ " + line.ljust(width - 4) + " │")
        lines.extend([
            "│" + " " * (width - 2) + "│",
            bottom,
        ])
        return "\n".join(_center_line(line, _terminal_width()) for line in lines)

    while True:
        prompt = "\n> "
        print(render_layout(build_panel(wrapped) + prompt), end="")
        response = _input().strip()
        if response == "EXIT":
            return False
        if response == "I UNDERSTAND":
            return True


def show_admin_panel() -> None:
    if not current_user_is_admin():
        panel = "ACCESS DENIED\nINSUFFICIENT PRIVILEGES"
        print(render_layout(panel), end="")
        _input("Return to menu: ")
        return
    owner_record = get_owner_record()
    admin_block = "No owner account found."

    if owner_record:
        admin_block = (
            f"username: {owner_record['username']}\n"
            f"created_at: {owner_record['created_at']}\n"
            f"hostname: {owner_record.get('hostname', 'unknown')}\n"
            f"machine_id: {owner_record.get('machine_id', 'unknown')}"
        )

    sessions_log = read_session_log(limit=200)
    activity_log = read_activity_log(limit=200)
    security_log = _read_security_log(limit=200)

    panel = (
        "[ owner control panel ]\n"
        f"{admin_block}\n\n"
        "[ login history ]\n"
        f"{security_log}\n\n"
        "[ sessions.log ]\n"
        f"{sessions_log}\n\n"
        "[ activity.log ]\n"
        f"{activity_log}"
    )
    print(render_layout(panel), end="")
    _input("Return to menu: ")


def show_auth_menu() -> bool:
    if not owner_exists():
        if _handle_owner_bootstrap():
            return True
        return False
    while True:
        menu = "[1] Login\n[2] Create Account\n[3] Exit\n\nSelect an option: "
        print(render_layout(menu), end="")
        choice = _input().strip()
        if choice == "3":
            return False
        if choice == "1":
            if _handle_login():
                return True
            continue
        if choice == "2":
            if _handle_register():
                return True
            continue
        print(render_layout("Invalid option."), end="")
    return False


def require_login() -> bool:
    while True:
        success = show_auth_menu()
        if success:
            return True
        return False


def _handle_owner_bootstrap() -> bool:
    while True:
        print(render_layout("Create Owner Account"), end="")
        username = _input("Username: ").strip()
        password = _getpass("Password: ").strip()
        confirm = _getpass("Confirm Password: ").strip()
        if not username or not password:
            print(render_layout("Username and password are required."), end="")
            continue
        if password != confirm:
            print(render_layout("Passwords do not match."), end="")
            continue
        ok, message = ensure_owner(username, password)
        if ok:
            user_id = get_user_id(username)
            set_current_user(username, "owner", user_id=user_id)
            log_action(username, "created owner account")
            return True
        print(render_layout(message), end="")
        return False


def _handle_login() -> bool:
    print(render_layout("Login"), end="")
    username = _input("Username: ").strip()
    password = _getpass("Password: ").strip()
    ok, message, role = authenticate(username, password)
    if ok:
        user_id = get_user_id(username)
        set_current_user(username, role, user_id=user_id)
        log_action(username, "login")
        return True
    print(render_layout(message), end="")
    return False


def _handle_register() -> bool:
    print(render_layout("Create Account"), end="")
    username = _input("Username: ").strip()
    password = _getpass("Password: ").strip()
    confirm = _getpass("Confirm Password: ").strip()
    if not username or not password:
        print(render_layout("Username and password are required."), end="")
        return False
    if password != confirm:
        print(render_layout("Passwords do not match."), end="")
        return False

    ok, message, role = register_user(username, password)
    if ok:
        user_id = get_user_id(username)
        set_current_user(username, role, user_id=user_id)
        log_action(username, "created account")
        return True
    print(render_layout(message), end="")
    return False


def _load_module_from_path(path: str, module_name: str) -> Optional[ModuleType]:
    try:
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as exc:
        LOG.exception("Plugin load failed: %s", exc)
        return None


def username_intelligence_ultra() -> None:
    subprocess.run(
        [
            "/home/hacker/BlackHaven/venv/bin/python",
            "/home/hacker/BlackHaven/skills/username_intelligence_ultra.py",
        ],
        check=False,
    )


def god_osint_core() -> None:
    subprocess.run(
        [
            "/home/hacker/BlackHaven/venv/bin/python",
            "/home/hacker/BlackHaven/skills/god_osint_core.py",
        ],
        check=False,
    )


def omega_scan() -> None:
    subprocess.run(
        [
            "/home/hacker/BlackHaven/venv/bin/python",
            "/home/hacker/BlackHaven/skills/omega_core.py",
        ],
        check=False,
    )


def discover_modules() -> List[Dict]:
    items: List[Dict] = []

    modules_pkg = "blackhaven.modules"
    from .. import modules as core_modules
    for modinfo in pkgutil.iter_modules(core_modules.__path__):
        module = importlib.import_module(f"{modules_pkg}.{modinfo.name}")
        if hasattr(module, "get_module"):
            info = module.get_module()
            if all(k in info for k in ("name", "description", "run")):
                items.append(info)

    plugins_dir = user_plugins_dir()
    if os.path.isdir(plugins_dir):
        for entry in os.listdir(plugins_dir):
            if not entry.endswith(".py"):
                continue
            path = os.path.join(plugins_dir, entry)
            mod = _load_module_from_path(path, f"plugin_{entry[:-3]}")
            if mod and hasattr(mod, "get_module"):
                info = mod.get_module()
                if all(k in info for k in ("name", "description", "run")):
                    items.append(info)

    order = [
        "Username Search",
        "Email Lookup",
        "Domain Info",
        "Port Scanner",
        "Password Checker",
        "System Info",
        "Intel Core",
    ]
    order_index = {name: idx for idx, name in enumerate(order)}
    items.sort(key=lambda x: order_index.get(x["name"], 999))
    return items


def _menu_text(items: List[Dict]) -> str:
    lines = []
    for item in items:
        key = item["key"]
        label = item["label"]
        lines.append(f"[ {key} ] {label}")
    return "\n".join(lines)


def _build_menu_items(modules: List[Dict]) -> List[Dict]:
    by_name = {m["name"]: m for m in modules}
    layout = [
        ("01", "Username Intelligence", "Username Search"),
        ("02", "Email Intelligence", "Email Lookup"),
        ("03", "Domain Intelligence", "Domain Info"),
        ("04", "Network Scanner", "Port Scanner"),
        ("05", "Username Intelligence ULTRA", None),
        ("06", "GOD OSINT CORE", None),
        ("07", "OMEGA SCAN", None),
        ("10", "Password Analyzer", "Password Checker"),
        ("09", "Intel Core", "Intel Core"),
        ("11", "Owner Control Panel", None),
        ("08", "System Intelligence", "System Info"),
        ("00", "Exit", None),
    ]
    items: List[Dict] = []
    for key, label, module_name in layout:
        module = by_name.get(module_name) if module_name else None
        items.append({"key": key, "label": label, "module": module})
    return items


def run_menu(modules: List[Dict]) -> Optional[Dict]:
    menu_items = _build_menu_items(modules)
    while True:
        menu = _menu_text(menu_items)
        prompt = "\nSelect an option: "
        print(render_layout(f"{menu}{prompt}"), end="")
        choice = _input().strip()

        if choice in {"0", "00"}:
            return None
        if choice == "11":
            show_admin_panel()
            continue
        if choice in {"5", "05"}:
            username_intelligence_ultra()
            continue
        if choice in {"6", "06"}:
            god_osint_core()
            continue
        if choice in {"7", "07"}:
            omega_scan()
            continue
        if not choice.isdigit():
            print(render_layout("Invalid option."), end="")
            continue

        selected = next((item for item in menu_items if item["key"] == choice), None)
        if selected and selected.get("module"):
            return selected["module"]

        print(render_layout("Invalid option."), end="")


def run_app() -> int:
    init(autoreset=True)
    setup_logging()

    modules = discover_modules()
    if not modules:
        print(render_layout("No modules found."), end="")
        return 1

    while True:
        selected = run_menu(modules)
        if selected is None:
            print(render_layout("Goodbye."), end="")
            return 0
        try:
            user = get_current_user()
            if user:
                log_action(user.username, f"executed {selected['name']}")
                if user.user_id is not None:
                    log_session(user.user_id, selected["name"])
            output = io.StringIO()
            with redirect_stdout(output), redirect_stderr(output):
                selected["run"]()

            result = output.getvalue().strip() or "Module ready."
            print(render_layout(result), end="")
            _input("Return to menu: ")
            continue
        except KeyboardInterrupt:
            print(render_layout("Cancelled."), end="")
            _input("Return to menu: ")
        except Exception as exc:
            LOG.exception("Module error: %s", exc)
            print(render_layout("Error: an unexpected error occurred."), end="")
            _input("Return to menu: ")
