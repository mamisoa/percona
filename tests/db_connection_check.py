"""
Minimal connectivity probe using credentials from .env.

Usage:
    uv run python tests/db_connection_check.py

Reads DB_USER, DB_PASSWORD, DB_HOSTS, DB_PORT from .env (or environment)
and attempts a short connection to each host. Returns non-zero if any host
fails to connect.
"""

from __future__ import annotations

import os
import sys
from typing import List, Tuple

import pymysql
from dotenv import load_dotenv


def load_env() -> Tuple[str, str, List[str], int]:
    """
    Load connection parameters from environment variables.

    Returns:
        Tuple with (user, password, hosts list, port).

    Raises:
        ValueError: if required variables are missing or invalid.
    """
    load_dotenv()
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    hosts_raw = os.getenv("DB_HOSTS")
    port_raw = os.getenv("DB_PORT", "3306")

    if not user or not password or not hosts_raw:
        raise ValueError("DB_USER, DB_PASSWORD, and DB_HOSTS must be set in environment/.env")

    hosts = [h.strip() for h in hosts_raw.split(",") if h.strip()]
    try:
        port = int(port_raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("DB_PORT must be an integer") from exc

    return user, password, hosts, port


def check_host(host: str, user: str, password: str, port: int) -> Tuple[bool, str]:
    """
    Attempt a simple MySQL connection to a host.

    Args:
        host: Hostname or IP to connect to.
        user: MySQL username.
        password: MySQL password.
        port: TCP port.

    Returns:
        (ok flag, message string).
    """
    try:
        conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            port=port,
            connect_timeout=5,
            cursorclass=pymysql.cursors.Cursor,
        )
        conn.close()
        return True, "OK"
    except Exception as exc:
        return False, f"ERROR: {exc}"


def main() -> None:
    """
    Run connectivity probe for all hosts from .env and exit non-zero on failure.
    """
    try:
        user, password, hosts, port = load_env()
    except ValueError as exc:
        print(f"[config error] {exc}")
        sys.exit(2)

    failures = 0
    for host in hosts:
        ok, msg = check_host(host, user, password, port)
        status = "✅" if ok else "❌"
        print(f"{status} {host}:{port} -> {msg}")
        if not ok:
            failures += 1

    sys.exit(0 if failures == 0 else 1)


if __name__ == "__main__":
    main()

