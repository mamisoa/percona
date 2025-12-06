"""
Data models and constants for Percona XtraDB Cluster checks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

# wsrep variables of interest fetched from each node.
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

