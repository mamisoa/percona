#!/usr/bin/env python3
"""
Check wsrep/Galera synchronization across Percona XtraDB Cluster nodes.

This script connects to a list of Percona XtraDB Cluster (Galera) nodes,
reads a set of wsrep_* status variables on each node, and evaluates whether
the cluster is healthy and synchronized.

Usage (with uv):
    uv sync
    uv run percona-cluster-check \
        --user root \
        --password 'your_password' \
        --hosts 192.168.20.230,192.168.20.231,192.168.20.232 \
        --port 3306

Environment variables via .env (loaded automatically):
    DB_USER, DB_PASSWORD, DB_HOSTS, DB_PORT

Parameters:
    --user: MySQL user used to connect to each node.
    --password: MySQL password (if omitted, you will be prompted).
    --hosts: Comma-separated list of node hostnames or IPs.
    --port: MySQL TCP port (default 3306).

Exit code:
    0 if the cluster is considered healthy and synchronized.
    1 otherwise.
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pymysql
from dotenv import load_dotenv

# wsrep variables we care about
STATUS_VARS = [
    "wsrep_cluster_size",
    "wsrep_cluster_status",
    "wsrep_connected",
    "wsrep_ready",
    "wsrep_local_state",
    "wsrep_local_state_comment",
    "wsrep_cluster_state_uuid",
    "wsrep_cluster_conf_id",
    "wsrep_last_applied",
    "wsrep_last_committed",
]


def load_env_defaults() -> EnvDefaults:
    """
    Load database connection defaults from environment variables via .env.

    Returns:
        EnvDefaults containing user, password, hosts, and port derived from
        DB_USER, DB_PASSWORD, DB_HOSTS, and DB_PORT. Missing values remain
        optional so CLI flags can still be required as needed.
    """
    load_dotenv()
    hosts = os.getenv("DB_HOSTS", "192.168.20.230,192.168.20.231,192.168.20.232")
    port_raw = os.getenv("DB_PORT", "3306")
    try:
        port = int(port_raw)
    except (TypeError, ValueError):
        port = 3306

    return EnvDefaults(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        hosts=hosts,
        port=port,
    )


@dataclass
class NodeStatus:
    """
    Hold wsrep status information for a single node.

    Attributes:
        host: Node hostname or IP address.
        ok: True if the node is individually considered healthy.
        vars: Dictionary of wsrep_* status variables for this node.
        error: Error message if the node could not be checked properly.
    """
    host: str
    ok: bool
    vars: Dict[str, Any]
    error: Optional[str] = None


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


def fetch_wsrep_status(host: str, user: str, password: str, port: int) -> NodeStatus:
    """
    Connect to a node and read selected wsrep status variables.

    Args:
        host: Hostname or IP of the MySQL/Percona node.
        user: MySQL username.
        password: MySQL password.
        port: MySQL TCP port.

    Returns:
        A NodeStatus object with the retrieved wsrep variables and
        a preliminary 'ok' flag based on local wsrep state.

    Errors:
        Connection or query issues are captured in the returned NodeStatus.error
        instead of being raised, so callers can continue evaluating other nodes.
    """
    vars_dict: Dict[str, Any] = {}

    try:
        conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            port=port,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
    except Exception as exc:
        return NodeStatus(host=host, ok=False, vars={}, error=f"Connection error: {exc}")

    try:
        with conn.cursor() as cursor:
            for var in STATUS_VARS:
                cursor.execute("SHOW GLOBAL STATUS LIKE %s", (var,))
                row = cursor.fetchone()
                if row is None:
                    vars_dict[var] = None
                else:
                    value = row["Value"]
                    # Convert some obvious integers
                    if var in (
                        "wsrep_cluster_size",
                        "wsrep_local_state",
                        "wsrep_cluster_conf_id",
                        "wsrep_last_applied",
                        "wsrep_last_committed",
                    ):
                        try:
                            value = int(value)
                        except (TypeError, ValueError):
                            pass
                    vars_dict[var] = value
    except Exception as exc:
        conn.close()
        return NodeStatus(host=host, ok=False, vars=vars_dict, error=f"Query error: {exc}")

    conn.close()

    # Local health check for this node
    ok = True
    if vars_dict.get("wsrep_cluster_status") != "Primary":
        ok = False
    if vars_dict.get("wsrep_connected") != "ON":
        ok = False
    if vars_dict.get("wsrep_ready") != "ON":
        ok = False
    if vars_dict.get("wsrep_local_state_comment") != "Synced":
        ok = False

    return NodeStatus(host=host, ok=ok, vars=vars_dict, error=None)


def evaluate_cluster(statuses: List[NodeStatus]) -> bool:
    """
    Evaluate global cluster health from the list of node statuses.

    Args:
        statuses: List of NodeStatus objects for all nodes.

    Returns:
        True if all nodes are healthy and the Galera cluster appears
        synchronized; False otherwise.
    """
    # Quick check: all nodes individually OK and no error
    for st in statuses:
        if st.error is not None:
            return False
        if not st.ok:
            return False

    # All nodes must agree on cluster size
    sizes = {st.vars.get("wsrep_cluster_size") for st in statuses}
    if len(sizes) != 1:
        return False

    # Cluster size must match number of nodes we are checking
    expected_size = len(statuses)
    size_val = next(iter(sizes))
    if size_val != expected_size:
        return False

    # All nodes must have same cluster UUID and conf_id
    uuids = {st.vars.get("wsrep_cluster_state_uuid") for st in statuses}
    conf_ids = {st.vars.get("wsrep_cluster_conf_id") for st in statuses}

    if len(uuids) != 1:
        return False

    if len(conf_ids) != 1:
        return False

    return True


def print_report(statuses: List[NodeStatus], cluster_ok: bool) -> None:
    """
    Print a human-readable report of node and cluster health.

    Args:
        statuses: List of NodeStatus objects for all nodes.
        cluster_ok: Result of the global cluster evaluation.
    """
    print("Percona XtraDB / Galera cluster status")
    print("=====================================\n")

    for idx, st in enumerate(statuses, start=1):
        print(f"Node #{idx}: {st.host}")
        if st.error:
            print(f"  STATUS: ERROR - {st.error}")
            print()
            continue

        print(f"  wsrep_cluster_status       : {st.vars.get('wsrep_cluster_status')}")
        print(f"  wsrep_cluster_size         : {st.vars.get('wsrep_cluster_size')}")
        print(f"  wsrep_connected            : {st.vars.get('wsrep_connected')}")
        print(f"  wsrep_ready                : {st.vars.get('wsrep_ready')}")
        print(f"  wsrep_local_state          : {st.vars.get('wsrep_local_state')} "
              f"({st.vars.get('wsrep_local_state_comment')})")
        print(f"  wsrep_cluster_state_uuid   : {st.vars.get('wsrep_cluster_state_uuid')}")
        print(f"  wsrep_cluster_conf_id      : {st.vars.get('wsrep_cluster_conf_id')}")
        print(f"  wsrep_last_applied         : {st.vars.get('wsrep_last_applied')}")
        print(f"  wsrep_last_committed       : {st.vars.get('wsrep_last_committed')}")
        print(f"  NODE HEALTH (local)        : {'OK' if st.ok else 'NOT OK'}")
        print()

    print("Cluster summary")
    print("---------------")
    if cluster_ok:
        print("GLOBAL STATUS: CLUSTER HEALTHY AND SYNCHRONIZED ✅")
    else:
        print("GLOBAL STATUS: CLUSTER PROBLEM DETECTED ❌")


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

    # Exit code for automation / monitoring
    sys.exit(0 if cluster_ok else 1)


if __name__ == "__main__":
    main()
