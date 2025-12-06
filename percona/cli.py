"""
Command-line interface entrypoint for the Percona cluster health check.
"""

from __future__ import annotations

import argparse
import getpass
import sys
from typing import List, Optional

from percona.env import EnvDefaults, load_env_defaults
from percona.models import NodeStatus
from percona.render import print_report
from percona.wsrep import evaluate_cluster, fetch_wsrep_status


def parse_args(env_defaults: EnvDefaults, argv: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parse command-line arguments for the script.

    Args:
        env_defaults: Defaults loaded from environment variables to prefill
            CLI parameters when flags are omitted.
        argv: Optional argument list for testing; falls back to sys.argv.

    Returns:
        An argparse.Namespace containing user, password, hosts, and port.
    """

    parser = argparse.ArgumentParser(
        description="Check wsrep/Galera synchronization of a Percona XtraDB Cluster."
    )
    parser.add_argument(
        "--user",
        required=env_defaults.user is None,
        default=env_defaults.user,
        help="MySQL user used to connect to each node (can come from DB_USER).",
    )
    parser.add_argument(
        "--password",
        default=env_defaults.password,
        help="MySQL password (prompted if missing; can come from DB_PASSWORD).",
    )
    parser.add_argument(
        "--hosts",
        default=env_defaults.hosts,
        help="Comma-separated list of node hostnames or IPs (or DB_HOSTS).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=env_defaults.port,
        help="MySQL TCP port (default: DB_PORT or 3306).",
    )
    return parser.parse_args(args=argv)


def main() -> None:
    """
    Main entry point of the script.

    - Parses command-line arguments.
    - Loads optional defaults from .env (DB_USER, DB_PASSWORD, DB_HOSTS, DB_PORT).
    - Connects to each node and collects wsrep status.
    - Evaluates cluster health.
    - Prints a report and exits with code 0 if healthy, 1 otherwise.
    """

    env_defaults = load_env_defaults()
    args = parse_args(env_defaults)

    if not args.password:
        args.password = getpass.getpass("MySQL password: ")

    hosts = [h.strip() for h in args.hosts.split(",") if h.strip()]

    statuses: List[NodeStatus] = []
    for host in hosts:
        status = fetch_wsrep_status(
            host=host,
            user=args.user,
            password=args.password,
            port=args.port,
        )
        statuses.append(status)

    cluster_ok = evaluate_cluster(statuses)
    print_report(statuses, cluster_ok)

    sys.exit(0 if cluster_ok else 1)


if __name__ == "__main__":
    main()

