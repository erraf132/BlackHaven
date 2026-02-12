"""
BlackHaven Framework
Copyright (c) 2026 erraf132 and Vyrn.exe Official
All rights reserved.
"""


from __future__ import annotations
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List
from core.utils import Output, safe_resolve
DEFAULT_TOP_PORTS = [
    20, 21, 22, 23, 25, 53, 67, 68, 69, 80,
    110, 111, 119, 123, 135, 137, 138, 139, 143, 161,
    389, 443, 445, 465, 514, 515, 587, 631, 993, 995,
    1080, 1433, 1521, 1723, 2049, 2082, 2083, 2100, 2222, 2483,
    2484, 3128, 3306, 3389, 3690, 4000, 4444, 4567, 5000, 5060,
    5432, 5900, 5985, 5986, 6000, 6379, 6667, 7001, 7002, 7070,
    8000, 8008, 8080, 8081, 8086, 8087, 8088, 8090, 8443, 8888,
    9000, 9001, 9002, 9042, 9200, 9300, 9418, 9999, 10000, 11211,
    27017, 27018, 27019, 28017, 30000, 33848, 49152, 49153, 49154,
    49155, 49156, 49157, 50000, 50070, 50075, 61616, 62078, 65535,
]
SERVICE_MAP = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    111: "RPC",
    135: "MSRPC",
    139: "NetBIOS",
    143: "IMAP",
    161: "SNMP",
    389: "LDAP",
    443: "HTTPS",
    445: "SMB",
    465: "SMTPS",
    587: "SMTP",
    993: "IMAPS",
    995: "POP3S",
    1433: "MSSQL",
    1521: "Oracle",
    3306: "MySQL",
    3389: "RDP",
    5432: "PostgreSQL",
    5900: "VNC",
    6379: "Redis",
    8080: "HTTP-Alt",
    8443: "HTTPS-Alt",
    27017: "MongoDB",
}
def _scan_port(ip: str, port: int, timeout: float = 0.6) -> bool:

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            return sock.connect_ex((ip, port)) == 0
    except Exception:
        return False


def run(target: str, config) -> Dict[str, Any]:
    """Run a threaded scan across the top 100 ports."""

    ip_address = safe_resolve(target)
    if not ip_address:
        raise RuntimeError("Unable to resolve target")

    ports = config.get("default_ports", DEFAULT_TOP_PORTS)
    timeout = config.get("timeout", 0.6)
    max_workers = config.get("thread_count", 64)

    Output.info(f"Resolved {target} -> {ip_address}")
    Output.info(f"Scanning {len(ports)} ports with {max_workers} threads...")

    open_ports: List[int] = []
    completed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(_scan_port, ip_address, port, timeout): port for port in ports}
        total = len(future_map)
        for future in as_completed(future_map):
            port = future_map[future]
            completed += 1
            Output.progress(f"Progress: {completed}/{total} ports scanned")
            if future.result():
                open_ports.append(port)
                Output.success(f"Port open: {port}")

    print()
    open_ports.sort()
    exposed = sorted({SERVICE_MAP.get(port, f"Port {port}") for port in open_ports})
    return {
        "target": target,
        "ip": ip_address,
        "open_ports": open_ports,
        "scanned_ports": len(ports),
        "exposed_services": exposed,
    }


def register(framework) -> None:
    """Module entrypoint registration."""

    framework.register_module("port_scanner", run)
