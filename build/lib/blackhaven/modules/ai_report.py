from __future__ import annotations

from blackhaven.ai.reporting import generate_report
from blackhaven.auth_pkg.logger import log_action
from blackhaven.auth_pkg.session import get_current_user


def run() -> None:
    user = get_current_user()
    if user:
        log_action(user.username, "generate ai report")

    target = input("Target name: ").strip()
    scope = input("Scope/authorization: ").strip()
    findings = input("Key findings (summary): ").strip()
    artifacts = input("Artifacts/links: ").strip()
    notes = input("Additional notes: ").strip()

    report = generate_report({
        "target": target,
        "scope": scope,
        "findings": findings,
        "artifacts": artifacts,
        "notes": notes,
    })
    print("\nReport generated and saved to results/reports/.")
    print("\n--- TXT ---\n")
    print(report["txt"])


def get_module():
    return {
        "name": "Generate AI Report",
        "description": "AI-generated investigation report",
        "run": run,
    }
