"""
NERO Universal Enterprise DevOps Automation Platform
Integration Tests for Local OCI Distribution Registry & Dynamic Resolution (A1-REG-001, A1-REG-002)
"""

import os
import unittest
from platform_core.adapters.registry.oci_adapter import OCIRegistryAdapter
from platform_core.engine.resolver import resolve_environment_context


class TestOCIRegistryAdapter(unittest.TestCase):

    def setUp(self):
        self.adapter = OCIRegistryAdapter(registry_endpoint="localhost:5100")

    def test_01_registry_ping_and_prerequisites(self):
        self.assertTrue(self.adapter.validate_prerequisites({}))

    def test_02_dynamic_registry_resolution(self):
        ctx_floci = resolve_environment_context(
            app_id="hotel-billing",
            environment="develop",
            target_platform="floci"
        )
        self.assertEqual(ctx_floci.oci_registry_endpoint, "localhost:5100")

        # In AWS test environment, provide mock account ID
        os.environ["AWS_DEVELOP_ACCOUNT_ID"] = "123456789012"
        os.environ["AWS_MANAGEMENT_ACCOUNT_ID"] = "999999999999"
        try:
            ctx_aws = resolve_environment_context(
                app_id="hotel-billing",
                environment="develop",
                target_platform="aws",
                region="ap-south-1"
            )
            self.assertEqual(ctx_aws.oci_registry_endpoint, "123456789012.dkr.ecr.ap-south-1.amazonaws.com")
        finally:
            os.environ.pop("AWS_DEVELOP_ACCOUNT_ID", None)
            os.environ.pop("AWS_MANAGEMENT_ACCOUNT_ID", None)

    def test_03_push_and_pull_lifecycle(self):
        # Push sample image
        res = self.adapter.tag_and_push(
            local_image="worker:rel-py-qual-01",
            target_repository="sample-python-worker",
            tag="test-integration"
        )
        self.assertTrue(res.pushed)
        self.assertTrue(res.digest.startswith("sha256:"))

        # Pull image
        pulled = self.adapter.pull_image("sample-python-worker", "test-integration")
        self.assertEqual(pulled, "localhost:5100/sample-python-worker:test-integration")

        # List catalog
        repos = self.adapter.list_repositories()
        self.assertIn("sample-python-worker", repos)


if __name__ == "__main__":
    unittest.main()
