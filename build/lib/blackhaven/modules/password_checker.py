from __future__ import annotations

import getpass
import math
import re
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple

from colorama import Fore, Style

from ._utils import export_results, get_logger

LOG = get_logger("password_checker")


def _charset_size(password: str) -> int:
    size = 0
    if re.search(r"[a-z]", password):
        size += 26
    if re.search(r"[A-Z]", password):
        size += 26
    if re.search(r"[0-9]", password):
        size += 10
    if re.search(r"[^a-zA-Z0-9]", password):
        size += 33
    return size


def _bruteforce_entropy(password: str) -> float:
    size = _charset_size(password)
    if size == 0:
        return 0.0
    return len(password) * math.log2(size)


def _pattern_issues(password: str) -> List[str]:
    issues = []
    lower = password.lower()

    if re.fullmatch(r"[a-z]+", password):
        issues.append("all lowercase")
    if re.fullmatch(r"[A-Z]+", password):
        issues.append("all uppercase")
    if re.fullmatch(r"[0-9]+", password):
        issues.append("all digits")

    if re.search(r"(.)\1\1", password):
        issues.append("repeating characters")

    if re.search(r"1234|2345|3456|4567|5678|6789|7890", password):
        issues.append("numeric sequence")
    if re.search(r"abcd|bcde|cdef|defg|efgh|fghi|ghij|hijk|ijkl|jklm|klmn|lmno|mnop|nopq|opqr|pqrs|qrst|rstu|stuv|tuvw|uvwx|vwxy|wxyz", lower):
        issues.append("alphabetic sequence")

    if len(password) < 8:
        issues.append("very short")
    elif len(password) < 12:
        issues.append("short")

    return issues


def _strength_label(score: int) -> str:
    if score <= 1:
        return "very weak"
    if score == 2:
        return "weak"
    if score == 3:
        return "okay"
    if score == 4:
        return "strong"
    return "very strong"


def run() -> None:
    pw = getpass.getpass("Enter password: ")
    if not pw:
        print("No password provided.")
        return

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            f_entropy = pool.submit(_bruteforce_entropy, pw)
            f_issues = pool.submit(_pattern_issues, pw)
            bf_entropy = f_entropy.result()
            issues = f_issues.result()
    except Exception as exc:
        LOG.exception("Password checks failed: %s", exc)
        print("Error: check failed. See ~/.blackhaven/results/blackhaven.log")
        return

    score = 0
    if len(pw) >= 12:
        score += 1
    if re.search(r"[a-z]", pw) and re.search(r"[A-Z]", pw):
        score += 1
    if re.search(r"[0-9]", pw):
        score += 1
    if re.search(r"[^a-zA-Z0-9]", pw):
        score += 1
    if bf_entropy >= 60:
        score += 1

    score = max(0, score - max(0, len(issues) - 1) // 2)

    label = _strength_label(score)
    print(f"Strength: {Fore.RED if score <=2 else Fore.GREEN}{label}{Style.RESET_ALL}")

    output_lines = [f"Strength: {label}", f"Entropy (bits): {bf_entropy:.1f}"]
    rows = [
        {"field": "Strength", "value": label},
        {"field": "Entropy_bits", "value": f"{bf_entropy:.1f}"},
    ]
    if issues:
        print("Issues:")
        for issue in sorted(set(issues)):
            print(f"- {issue}")
            output_lines.append(f"Issue: {issue}")
            rows.append({"field": "Issue", "value": issue})

    paths = export_results("password_checker", output_lines, rows)
    print("\nSaved results to:")
    for p in paths:
        print(f"- {p}")


def get_module():
    return {
        "name": "Password Checker",
        "description": "Estimate password strength",
        "run": run,
    }
