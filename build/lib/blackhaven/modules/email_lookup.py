from __future__ import annotations

import hashlib
import re
import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple

from colorama import Fore, Style

from blackhaven.auth_pkg.logger import log_action
from blackhaven.auth_pkg.session import get_current_user
from ._utils import export_results, get_logger

LOG = get_logger("email_lookup")

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def _mx_lookup(domain: str) -> str:
    try:
        result = subprocess.run(
            ["nslookup", "-type=mx", domain],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        if result.returncode == 0 and "mail exchanger" in result.stdout.lower():
            return "MX records found"
        if result.returncode == 0:
            return "MX records not found"
        return f"MX lookup error (code {result.returncode})"
    except Exception as exc:
        LOG.exception("MX lookup failed: %s", exc)
        return "MX lookup failed"


def _domain_resolves(domain: str) -> str:
    try:
        socket.getaddrinfo(domain, None)
        return "Domain resolves"
    except socket.gaierror:
        return "Domain does not resolve"
    except Exception as exc:
        LOG.exception("Domain resolve failed: %s", exc)
        return "Domain resolve failed"


def _gravatar_check(email: str) -> str:
    try:
        email_hash = hashlib.md5(email.strip().lower().encode("utf-8")).hexdigest()
        url = f"https://www.gravatar.com/avatar/{email_hash}?d=404"
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", url],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        if result.stdout.strip() == "200":
            return "Gravatar profile found"
        return "No Gravatar profile"
    except Exception as exc:
        LOG.exception("Gravatar check failed: %s", exc)
        return "Gravatar check failed"


def run() -> None:
    email = input("Email to lookup: ").strip()
    if not email:
        print("No email provided.")
        return
    if not EMAIL_RE.fullmatch(email):
        print("Invalid email format.")
        return

    domain = email.split("@", 1)[1]
    user = get_current_user()
    if user:
        log_action(user.username, f"email lookup {email}")
    print("\nRunning checks...")

    tasks = {
        "Domain resolve": lambda: _domain_resolves(domain),
        "MX lookup": lambda: _mx_lookup(domain),
        "Gravatar": lambda: _gravatar_check(email),
    }

    results: List[Tuple[str, str]] = []
    try:
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {pool.submit(fn): name for name, fn in tasks.items()}
            for fut in as_completed(futures):
                name = futures[fut]
                try:
                    results.append((name, fut.result()))
                except Exception as exc:
                    LOG.exception("Task failed: %s", exc)
                    results.append((name, "Error"))
    except Exception as exc:
        LOG.exception("Threaded checks failed: %s", exc)
        print("Error: failed during checks. See ~/.blackhaven/results/blackhaven.log")
        return

    output_lines = [f"Email: {email}", f"Domain: {domain}", ""]
    rows = [{"check": "Email", "value": email}, {"check": "Domain", "value": domain}]
    for name, value in results:
        line = f"- {name}: {value}"
        color = Fore.GREEN if "found" in value.lower() or "resolves" in value.lower() else Fore.YELLOW
        print(f"{color}{line}{Style.RESET_ALL}")
        output_lines.append(line)
        rows.append({"check": name, "value": value})

    paths = export_results("email_lookup", output_lines, rows)
    print("\nSaved results to:")
    for p in paths:
        print(f"- {p}")


def get_module():
    return {
        "name": "Email Lookup",
        "description": "Basic OSINT checks for an email address",
        "run": run,
    }
