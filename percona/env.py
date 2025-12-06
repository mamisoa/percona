"""
Environment helpers for cluster checks.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

DEFAULT_HOSTS = "192.168.20.230,192.168.20.231,192.168.20.232"
DEFAULT_PORT = 3306


@dataclass
class EnvDefaults:
    """
    Hold optional database connection parameters sourced from environment.

    Attributes:
        user: Username provided via DB_USER.
        password: Password provided via DB_PASSWORD.
        hosts: Comma-separated host list from DB_HOSTS.
        port: TCP port from DB_PORT.
    """

    user: Optional[str]
    password: Optional[str]
    hosts: str
    port: int


def load_env_defaults() -> EnvDefaults:
    """
    Load database connection defaults from environment variables via .env.

    Returns:
        EnvDefaults containing user, password, hosts, and port derived from
        DB_USER, DB_PASSWORD, DB_HOSTS, and DB_PORT. Missing values remain
        optional so CLI flags can still be required as needed.
    """

    load_dotenv()
    hosts = os.getenv("DB_HOSTS", DEFAULT_HOSTS)
    port_raw = os.getenv("DB_PORT", str(DEFAULT_PORT))
    try:
        port = int(port_raw)
    except (TypeError, ValueError):
        port = DEFAULT_PORT

    return EnvDefaults(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        hosts=hosts,
        port=port,
    )

