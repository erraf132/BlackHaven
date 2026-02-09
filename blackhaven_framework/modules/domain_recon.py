"""
BlackHaven Framework
Copyright (c) 2026 erraf132 and Vyrn.exe Official
All rights reserved.
"""


from __future__ import annotations
from typing import Any, Dict, List
import dns.resolver
import whois
from core.utils import Output, safe_resolve
def _dns_lookup(domain: str, record_type: str, timeout: float) -> List[str]:

    try:
        answers = dns.resolver.resolve(domain, record_type, lifetime=timeout)
        return [answer.to_text() for answer in answers]
    except Exception:
        return []


def run(target: str, config) -> Dict[str, Any]:
    """Run domain intelligence tasks."""

    timeout = config.get("timeout", 4)
    Output.info("Resolving domain...")
    ip_address = safe_resolve(target)

    Output.info("Performing WHOIS lookup...")
    try:
        whois_data = whois.whois(target)
        whois_summary = {
            "domain_name": whois_data.domain_name,
            "registrar": whois_data.registrar,
            "creation_date": whois_data.creation_date,
            "expiration_date": whois_data.expiration_date,
            "name_servers": whois_data.name_servers,
        }
    except Exception as exc:
        whois_summary = {"error": str(exc)}

    Output.info("Gathering DNS records...")
    dns_records = {
        "A": _dns_lookup(target, "A", timeout),
        "AAAA": _dns_lookup(target, "AAAA", timeout),
        "MX": _dns_lookup(target, "MX", timeout),
        "NS": _dns_lookup(target, "NS", timeout),
        "TXT": _dns_lookup(target, "TXT", timeout),
    }

    return {
        "target": target,
        "resolved_ip": ip_address,
        "whois": whois_summary,
        "dns": dns_records,
    }


def register(framework) -> None:
    """Module entrypoint registration."""

    framework.register_module("domain_recon", run)
