from __future__ import annotations

from typing import Dict, List


def correlate(inputs: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Correlate basic OSINT entities to surface simple patterns.

    Inputs keys may include: usernames, emails, domains, ips.
    """
    usernames = inputs.get("usernames", [])
    emails = inputs.get("emails", [])
    domains = inputs.get("domains", [])
    ips = inputs.get("ips", [])

    findings: List[str] = []

    for email in emails:
        if "@" in email:
            local, domain = email.split("@", 1)
            if domain and domain not in domains:
                findings.append(f"Email domain observed: {domain}")
            for username in usernames:
                if username and username.lower() in local.lower():
                    findings.append(f"Username '{username}' appears in email '{email}'.")

    for domain in domains:
        for username in usernames:
            if username and username.lower() in domain.lower():
                findings.append(f"Username '{username}' appears in domain '{domain}'.")

    if ips:
        findings.append(f"IP addresses provided: {', '.join(ips)}")

    risk = []
    if len(emails) > 3:
        risk.append("High volume of email identifiers observed.")
    if len(domains) > 3:
        risk.append("Multiple domains detected; validate ownership.")
    if len(ips) > 0:
        risk.append("Validate IP ownership and authorization before probing.")

    return {
        "connections": findings,
        "risk_indicators": risk,
    }
