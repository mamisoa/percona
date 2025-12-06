"""
Core logic for fetching and evaluating wsrep status from cluster nodes.
"""

from __future__ import annotations

from typing import Any, Dict, List

import pymysql

from percona.models import STATUS_VARS, NodeStatus


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
    except Exception as exc:  # pragma: no cover - network errors not deterministic
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
    except Exception as exc:  # pragma: no cover - network errors not deterministic
        conn.close()
        return NodeStatus(host=host, ok=False, vars=vars_dict, error=f"Query error: {exc}")

    conn.close()

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

    for st in statuses:
        if st.error is not None:
            return False
        if not st.ok:
            return False

    sizes = {st.vars.get("wsrep_cluster_size") for st in statuses}
    if len(sizes) != 1:
        return False

    expected_size = len(statuses)
    size_val = next(iter(sizes))
    if size_val != expected_size:
        return False

    uuids = {st.vars.get("wsrep_cluster_state_uuid") for st in statuses}
    conf_ids = {st.vars.get("wsrep_cluster_conf_id") for st in statuses}

    if len(uuids) != 1:
        return False

    if len(conf_ids) != 1:
        return False

    return True


def compute_warnings(statuses: List[NodeStatus], drift_threshold_pct: float = 3.0) -> Dict[str, List[str]]:
    """
    Compute warning messages per node for replication lag and cross-node drift.

    Args:
        statuses: List of NodeStatus objects for all nodes.
        drift_threshold_pct: Percentage drift (behind max committed) to flag a warning.

    Returns:
        Mapping of host to a list of warning messages. Empty lists mean no warnings.
    """

    warnings: Dict[str, List[str]] = {st.host: [] for st in statuses}

    for st in statuses:
        applied = st.vars.get("wsrep_last_applied")
        committed = st.vars.get("wsrep_last_committed")
        if applied is not None and committed is not None and applied != committed:
            warnings[st.host].append(
                f"Replication lag: applied={applied}, committed={committed}"
            )

    committed_values = [
        st.vars.get("wsrep_last_committed")
        for st in statuses
        if isinstance(st.vars.get("wsrep_last_committed"), int)
    ]
    if committed_values:
        reference = max(committed_values)
        if reference > 0:
            for st in statuses:
                committed = st.vars.get("wsrep_last_committed")
                if not isinstance(committed, int):
                    continue
                drift_pct = ((reference - committed) / reference) * 100
                if drift_pct > drift_threshold_pct:
                    warnings[st.host].append(
                        f"Drift {drift_pct:.2f}% behind max committed ({committed} vs {reference})"
                    )

    return warnings

