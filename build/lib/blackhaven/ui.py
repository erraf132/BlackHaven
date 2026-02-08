from __future__ import annotations

import importlib
import importlib.util
import io
import os
import pkgutil
import time
from importlib import resources
from types import ModuleType
from typing import Dict, List, Optional

from colorama import init
from prompt_toolkit import Application
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Layout, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.styles import Style as PTStyle
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .modules._utils import get_logger, setup_logging, user_plugins_dir

LOG = get_logger("BlackHaven")


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


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


def discover_modules() -> List[Dict]:
    items: List[Dict] = []

    modules_pkg = "blackhaven.modules"
    from . import modules as core_modules
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
    ]
    order_index = {name: idx for idx, name in enumerate(order)}
    items.sort(key=lambda x: order_index.get(x["name"], 999))
    return items


def display_banner() -> None:
    console = Console()
    banner = [
        "  ██████╗ ██╗      █████╗  ██████╗██╗  ██╗██╗  ██╗ █████╗ ██╗   ██╗███████╗███╗   ██╗",
        "  ██╔══██╗██║     ██╔══██╗██╔════╝██║ ██╔╝██║ ██╔╝██╔══██╗██║   ██║██╔════╝████╗  ██║",
        "  ██████╔╝██║     ███████║██║     █████╔╝ █████╔╝ ███████║██║   ██║█████╗  ██╔██╗ ██║",
        "  ██╔══██╗██║     ██╔══██║██║     ██╔═██╗ ██╔═██╗ ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║",
        "  ██████╔╝███████╗██║  ██║╚██████╗██║  ██╗██║  ██╗██║  ██║╚██████╔╝███████╗██║ ╚████║",
        "  ╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝",
    ]

    clear_screen()
    for line in banner:
        text = Text()
        for ch in line:
            text.append(ch, style="bold red")
            console.print(text, end="\r")
            time.sleep(0.002)
        console.print(text)
    console.print(Text("BlackHaven - OSINT & Security Auditing", style="white"))


def loading_animation(duration: float = 0.8) -> None:
    console = Console()
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    start = time.time()
    idx = 0
    while time.time() - start < duration:
        console.print(f"[red]{frames[idx % len(frames)]}[/red] Initializing BlackHaven...", end="\r")
        time.sleep(0.05)
        idx += 1
    console.print(" " * 60, end="\r")


def display_disclaimer() -> None:
    console = Console()
    try:
        text = resources.files(__package__).joinpath("DISCLAIMER.txt").read_text(encoding="utf-8")
    except Exception:
        text = "Disclaimer not available."

    panel = Panel(
        Text(text.strip(), style="red"),
        title=Text("DISCLAIMER", style="bold red"),
        border_style="red",
        padding=(1, 2),
    )
    clear_screen()
    console.print(panel)
    console.print(Text("Press ENTER to continue...", style="white on black"))
    input()


def _render_menu_ansi(items: List[Dict], selected: int) -> str:
    width = 76
    buffer = io.StringIO()
    console = Console(
        file=buffer,
        force_terminal=True,
        color_system="truecolor",
        width=width,
    )

    title = Text("BlackHaven", style="bold red")
    subtitle = Text("OSINT & Security Auditing", style="white")

    lines: List[Text] = []
    for idx, item in enumerate(items):
        label = f"{idx + 1}. {item['name']} - {item['description']}"
        if idx == selected:
            line = Text(label, style="bold black on red")
        else:
            line = Text(label, style="white")
        lines.append(line)

    panel_content = Text.assemble(subtitle, "\n\n")
    for line in lines:
        panel_content.append(line)
        panel_content.append("\n")

    panel = Panel(
        panel_content,
        title=title,
        border_style="red",
        padding=(1, 2),
    )

    console.print(panel)
    console.print(Text("BlackHaven v1.0 | OSINT Toolkit", style="white on black"))

    return buffer.getvalue()


def run_menu(modules: List[Dict]) -> Optional[Dict]:
    items = modules + [
        {"name": "Exit", "description": "Close BlackHaven", "run": None}
    ]
    selected = 0

    control = FormattedTextControl(ANSI(_render_menu_ansi(items, selected)))

    def refresh() -> None:
        control.text = ANSI(_render_menu_ansi(items, selected))

    kb = KeyBindings()

    @kb.add("up")
    def _up(event) -> None:
        nonlocal selected
        selected = (selected - 1) % len(items)
        refresh()
        event.app.invalidate()

    @kb.add("down")
    def _down(event) -> None:
        nonlocal selected
        selected = (selected + 1) % len(items)
        refresh()
        event.app.invalidate()

    @kb.add("enter")
    def _enter(event) -> None:
        event.app.exit(result=selected)

    @kb.add("c-c")
    def _exit(event) -> None:
        event.app.exit(result=len(items) - 1)

    style = PTStyle.from_dict({
        "": "bg:black",
    })

    app = Application(
        layout=Layout(HSplit([Window(control)])),
        key_bindings=kb,
        style=style,
        full_screen=True,
    )

    result = app.run()
    if result is None:
        return None
    if result == len(items) - 1:
        return None
    return items[result]


def run_app() -> int:
    init(autoreset=True)
    setup_logging()

    modules = discover_modules()
    if not modules:
        print("No modules found.")
        return 1

    clear_screen()
    display_disclaimer()
    loading_animation()
    display_banner()
    time.sleep(0.2)

    while True:
        clear_screen()
        selected = run_menu(modules)
        if selected is None:
            clear_screen()
            print("Goodbye.")
            return 0
        try:
            selected["run"]()
        except KeyboardInterrupt:
            print("\nCancelled.")
        except Exception as exc:
            LOG.exception("Module error: %s", exc)
            print("Error: an unexpected error occurred. Check ~/.blackhaven/results/blackhaven.log")
        input("\nPress Enter to continue...")
