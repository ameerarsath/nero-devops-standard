"""
NERO Platform - Dynamic Port Allocation & Catalog Registration Tests (A2-CAT-001 - A2-CAT-004)
Tests dynamic port allocator, collision detection, catalog dynamic registration, and security tier allowlists.
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from platform_core.engine.catalog import ApplicationCatalog, PortAllocationManager, CatalogApplication
from platform_core.engine.models import ApplicationSpec
from platform_core.engine.parser import parse_and_validate_spec
from platform_core.engine.resolver import resolve_environment_context
from platform_core.engine.errors import ConfigurationError, SecurityPolicyError


class TestDynamicPortAllocationAndCatalog(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.catalog_path = Path(self.temp_dir) / "applications.yaml"
        # Seed test catalog
        seed_yaml = """
version: "2.0"
applications:
  - id: "hotel-billing"
    display_name: "Hotel Billing"
    trusted_repository: "https://github.com/ameerarsath/billing-system.git"
    spec_path: "app.spec.yaml"
    allowed_branches: ["main", "master"]
    allowed_environments: ["develop", "qa", "prod"]
    allowed_platforms: ["floci", "aws"]
    allowed_topologies: ["multi_account"]
    permitted_build_adapters: ["dockerfile", "node"]
    permitted_deployment_adapters: ["ecs", "s3-static"]
    security_tier: "tier-1-business-critical"
    allocated_ports:
      develop: 8085
      qa: 8087
      prod: 8089
"""
        with open(self.catalog_path, "w", encoding="utf-8") as f:
            f.write(seed_yaml)
        self.catalog = ApplicationCatalog(str(self.catalog_path))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_existing_ports_retrieval(self):
        """Verifies retrieving ports for pre-registered applications."""
        dev_port = self.catalog.get_port_for_environment("hotel-billing", "develop")
        qa_port = self.catalog.get_port_for_environment("hotel-billing", "qa")
        prod_port = self.catalog.get_port_for_environment("hotel-billing", "prod")

        self.assertEqual(dev_port, 8085)
        self.assertEqual(qa_port, 8087)
        self.assertEqual(prod_port, 8089)

    def test_02_allocate_new_ports_without_collision(self):
        """Verifies PortAllocationManager assigns available non-colliding port blocks."""
        ports = PortAllocationManager.allocate_ports(
            app_id="new-service",
            catalog_entries=self.catalog._entries,
            environments=["develop", "qa", "prod"]
        )
        expected_dev = 8111 if PortAllocationManager.is_port_in_use_os(8101) else 8101
        self.assertEqual(ports["develop"], expected_dev)
        self.assertEqual(ports["qa"], expected_dev + 1)
        self.assertEqual(ports["prod"], expected_dev + 2)

    def test_03_detect_requested_port_collision(self):
        """Verifies that requesting a port already owned by another service raises ConfigurationError."""
        with self.assertRaises(ConfigurationError) as ctx:
            PortAllocationManager.allocate_ports(
                app_id="rogue-service",
                catalog_entries=self.catalog._entries,
                environments=["develop"],
                requested_port=8085  # Already owned by hotel-billing in develop
            )
        self.assertIn("Port collision", str(ctx.exception))

    def test_04_register_application_dynamic(self):
        """Verifies dynamic application registration updates catalog and allocates ports."""
        root = Path(__file__).resolve().parent.parent.parent
        node_spec_path = root / "applications" / "sample-node-service" / "app.spec.yaml"
        spec = parse_and_validate_spec(str(node_spec_path), workspace_root=str(root))

        entry = self.catalog.register_application(
            spec=spec,
            trusted_repository="https://github.com/enterprise/sample-node-service.git",
            security_tier="tier-2-standard"
        )

        self.assertEqual(entry.id, "sample-node-service")
        self.assertIn("develop", entry.allocated_ports)
        # Port should be allocated from 8100 block
        self.assertGreaterEqual(entry.allocated_ports["develop"], 8100)

        # Verify entry is retrievable
        fetched = self.catalog.get_application("sample-node-service")
        self.assertEqual(fetched.id, "sample-node-service")
        self.assertEqual(fetched.security_tier, "tier-2-standard")

    def test_05_security_tier_adapter_allowlist_enforcement(self):
        """Verifies that tier-1 applications cannot use unpermitted build adapters."""
        root = Path(__file__).resolve().parent.parent.parent
        worker_spec_path = root / "applications" / "sample-python-worker" / "app.spec.yaml"
        spec = parse_and_validate_spec(str(worker_spec_path), workspace_root=str(root))

        # Change adapter to python (prohibited in tier-1)
        spec.spec.components[0].build.adapter = "python"

        with self.assertRaises(SecurityPolicyError) as ctx:
            self.catalog.register_application(
                spec=spec,
                trusted_repository="https://github.com/enterprise/sample-python-worker.git",
                security_tier="tier-1-business-critical"
            )
        self.assertIn("prohibited under 'tier-1-business-critical'", str(ctx.exception))

    def test_06_os_socket_probe_detects_bound_port(self):
        """Verifies PortAllocationManager skips port blocks where active OS TCP sockets are bound (REMED-A2-002)."""
        import socket
        # Bind candidate port 8101 (which would be develop port in candidate block 8100)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", 8101))
            sock.listen(1)

            # Allocation should detect port 8101 is bound and skip to block 8110
            ports = PortAllocationManager.allocate_ports(
                app_id="conflict-avoidance-service",
                catalog_entries=self.catalog._entries,
                environments=["develop", "qa", "prod"]
            )
            self.assertEqual(ports["develop"], 8111)
            self.assertEqual(ports["qa"], 8112)
            self.assertEqual(ports["prod"], 8113)
        finally:
            sock.close()

    def test_07_requested_port_collision_on_active_os_socket(self):
        """Verifies that requesting a port actively bound on host OS raises ConfigurationError (REMED-A2-002)."""
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", 8155))
            sock.listen(1)

            with self.assertRaises(ConfigurationError) as ctx:
                PortAllocationManager.allocate_ports(
                    app_id="socket-colliding-service",
                    catalog_entries=self.catalog._entries,
                    environments=["develop"],
                    requested_port=8155
                )
            self.assertIn("actively bound by an OS process", str(ctx.exception))
        finally:
            sock.close()

    def test_08_catalog_file_lock_concurrency_protection(self):
        """Verifies catalog file lock and atomic replace ensure catalog consistency (REMED-A2-002)."""
        from platform_core.engine.catalog import catalog_file_lock
        lock_path = self.catalog_path.with_suffix(".lock")

        # Test acquiring lock
        with catalog_file_lock(lock_path):
            self.assertTrue(lock_path.exists())

        # Test registering app produces valid YAML with atomic replace
        root = Path(__file__).resolve().parent.parent.parent
        node_spec_path = root / "applications" / "sample-node-service" / "app.spec.yaml"
        spec = parse_and_validate_spec(str(node_spec_path), workspace_root=str(root))

        entry = self.catalog.register_application(
            spec=spec,
            trusted_repository="https://github.com/enterprise/sample-node-service.git"
        )
        self.assertEqual(entry.id, "sample-node-service")
        self.assertTrue(self.catalog_path.is_file())
        # .tmp should not be left behind
        self.assertFalse(self.catalog_path.with_suffix(".tmp").exists())


if __name__ == "__main__":
    unittest.main()
