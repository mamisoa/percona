"""
FastAPI application exposing Percona cluster health endpoints.

The API surfaces the same wsrep status checks used by the CLI, providing:
- a simple health check
- node listing from DB_HOSTS (.env aware)
- per-node status
- global cluster status (plus warnings)
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple

from fastapi import FastAPI, HTTPException

from percona.env import EnvDefaults, load_env_defaults
from percona.models import NodeStatus
from percona.wsrep import compute_warnings, evaluate_cluster, fetch_wsrep_status

__all__ = ["create_app"]


def create_app(
    fetch_status_func: Callable[[str, str, str, int], NodeStatus] = fetch_wsrep_status,
    evaluate_cluster_func: Callable[[List[NodeStatus]], bool] = evaluate_cluster,
    compute_warnings_func: Callable[[List[NodeStatus]], Dict[str, List[str]]] = compute_warnings,
) -> FastAPI:
    """
    Build a FastAPI application exposing cluster health endpoints.

    Args:
        fetch_status_func: Callable used to fetch wsrep status from a node.
        evaluate_cluster_func: Callable that evaluates overall cluster health.
        compute_warnings_func: Callable that generates per-node warning messages.

    Returns:
        A FastAPI application instance with health and cluster routes registered.
    """

    app = FastAPI(
        title="Percona Cluster API",
        version="0.1.0",
        description="Serve Percona XtraDB Cluster status via HTTP.",
    )

    def _split_hosts(raw_hosts: str) -> List[str]:
        """Split a comma-separated host string into a clean list."""
        return [host.strip() for host in raw_hosts.split(",") if host.strip()]

    def _validate_env(require_credentials: bool) -> Tuple[EnvDefaults, List[str]]:
        """
        Load environment defaults and validate presence of hosts (and credentials).

        Args:
            require_credentials: Whether DB_USER and DB_PASSWORD must be present.

        Returns:
            Tuple containing the loaded EnvDefaults and the parsed host list.

        Raises:
            HTTPException: When required configuration is missing.
        """

        env_defaults = load_env_defaults()
        hosts = _split_hosts(env_defaults.hosts)

        if not hosts:
            raise HTTPException(
                status_code=500,
                detail="DB_HOSTS must define at least one host in environment or .env",
            )

        if require_credentials and (not env_defaults.user or not env_defaults.password):
            raise HTTPException(
                status_code=500,
                detail="DB_USER and DB_PASSWORD must be set in environment or .env",
            )

        return env_defaults, hosts

    def _serialize_status(status: NodeStatus) -> Dict[str, Any]:
        """
        Convert a NodeStatus into a JSON-serializable mapping.

        Args:
            status: NodeStatus instance to serialize.

        Returns:
            Dictionary containing host, ok flag, wsrep variables, and optional error.
        """

        return {
            "host": status.host,
            "ok": status.ok,
            "vars": status.vars,
            "error": status.error,
        }

    @app.get("/health")
    def health() -> Dict[str, str]:
        """Lightweight API health probe."""

        return {"status": "ok"}

    @app.get("/nodes")
    def list_nodes() -> Dict[str, Any]:
        """List configured nodes from DB_HOSTS along with the port."""

        env_defaults, hosts = _validate_env(require_credentials=False)
        return {"hosts": hosts, "port": env_defaults.port, "count": len(hosts)}

    @app.get("/nodes/{host}/status")
    def node_status(host: str) -> Dict[str, Any]:
        """
        Fetch wsrep status for a specific node.

        Args:
            host: Node hostname or IP to check. Must be present in DB_HOSTS.

        Returns:
            Serialized NodeStatus for the requested host.

        Raises:
            HTTPException: If host is unknown or credentials are missing.
        """

        env_defaults, hosts = _validate_env(require_credentials=True)
        if host not in hosts:
            raise HTTPException(
                status_code=404,
                detail=f"Host '{host}' is not listed in DB_HOSTS",
            )

        status = fetch_status_func(
            host=host,
            user=env_defaults.user or "",
            password=env_defaults.password or "",
            port=env_defaults.port,
        )
        return _serialize_status(status)

    @app.get("/cluster/status")
    def cluster_status() -> Dict[str, Any]:
        """
        Aggregate cluster health across all configured nodes.

        Returns:
            Mapping with overall ok flag, serialized node statuses, and warnings.
        """

        env_defaults, hosts = _validate_env(require_credentials=True)
        statuses: List[NodeStatus] = []
        for target in hosts:
            statuses.append(
                fetch_status_func(
                    host=target,
                    user=env_defaults.user or "",
                    password=env_defaults.password or "",
                    port=env_defaults.port,
                )
            )

        cluster_ok = evaluate_cluster_func(statuses)
        warnings = compute_warnings_func(statuses)
        return {
            "ok": cluster_ok,
            "nodes": [_serialize_status(status) for status in statuses],
            "warnings": warnings,
        }

    return app


app = create_app()

