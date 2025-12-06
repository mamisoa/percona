from __future__ import annotations

import os
import unittest
from typing import Dict, List

from fastapi.testclient import TestClient

from percona.api import create_app
from percona.models import NodeStatus


class TestApi(unittest.TestCase):
    """Validate FastAPI endpoints for Percona cluster status."""

    def setUp(self) -> None:
        """Prepare environment variables and a test client with fakes."""

        self._env_backup = os.environ.copy()
        os.environ["DB_USER"] = "api_user"
        os.environ["DB_PASSWORD"] = "api_password"
        os.environ["DB_HOSTS"] = "node1,node2"
        os.environ["DB_PORT"] = "3306"

        statuses: Dict[str, NodeStatus] = {
            "node1": NodeStatus(
                host="node1",
                ok=True,
                vars={"wsrep_cluster_status": "Primary", "wsrep_ready": "ON"},
                error=None,
            ),
            "node2": NodeStatus(
                host="node2",
                ok=False,
                vars={"wsrep_cluster_status": "Non-Primary", "wsrep_ready": "OFF"},
                error="Query error",
            ),
        }

        def fake_fetch(host: str, user: str, password: str, port: int) -> NodeStatus:
            """Return deterministic NodeStatus objects per host."""

            self.assertEqual(user, "api_user")
            self.assertEqual(password, "api_password")
            self.assertEqual(port, 3306)
            return statuses[host]

        def fake_evaluate(statuses_list: List[NodeStatus]) -> bool:
            """Evaluate cluster health by requiring all nodes to be ok."""

            return all(status.ok for status in statuses_list)

        def fake_warnings(statuses_list: List[NodeStatus]) -> Dict[str, List[str]]:
            """Produce empty warnings for each node."""

            return {status.host: [] for status in statuses_list}

        self.client = TestClient(
            create_app(
                fetch_status_func=fake_fetch,
                evaluate_cluster_func=fake_evaluate,
                compute_warnings_func=fake_warnings,
            )
        )

    def tearDown(self) -> None:
        """Restore environment after each test."""

        os.environ.clear()
        os.environ.update(self._env_backup)

    def test_health_endpoint(self) -> None:
        """Health endpoint should return a simple ok status."""

        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_list_nodes_uses_env_hosts(self) -> None:
        """Nodes endpoint should reflect DB_HOSTS and DB_PORT."""

        response = self.client.get("/nodes")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["hosts"], ["node1", "node2"])
        self.assertEqual(payload["port"], 3306)
        self.assertEqual(payload["count"], 2)

    def test_node_status_known_host(self) -> None:
        """Per-node endpoint should serialize NodeStatus for known hosts."""

        response = self.client.get("/nodes/node1/status")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["host"], "node1")
        self.assertEqual(payload["error"], None)

    def test_node_status_unknown_host(self) -> None:
        """Per-node endpoint should return 404 for unknown hosts."""

        response = self.client.get("/nodes/unknown/status")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Host 'unknown'", response.json().get("detail", ""))

    def test_cluster_status_aggregates_nodes(self) -> None:
        """Cluster endpoint should include aggregated statuses and warnings."""

        response = self.client.get("/cluster/status")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["ok"])
        self.assertEqual(len(payload["nodes"]), 2)
        self.assertEqual(payload["warnings"], {"node1": [], "node2": []})

    def test_missing_credentials_returns_error(self) -> None:
        """Cluster endpoint should fail when credentials are absent."""

        os.environ.pop("DB_USER", None)
        os.environ.pop("DB_PASSWORD", None)
        response = self.client.get("/cluster/status")
        self.assertEqual(response.status_code, 500)
        self.assertIn("DB_USER and DB_PASSWORD", response.json().get("detail", ""))


if __name__ == "__main__":
    unittest.main()

