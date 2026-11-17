"""
NERO Universal Enterprise DevOps Automation Platform
Unit Tests for BasePlatformAdapter Interface & Polymorphism (A1-FND-001)
"""

import unittest
from platform_core.adapters.base import (
    BasePlatformAdapter,
    AdapterRequest,
    AdapterResult
)
from platform_core.adapters import BaseAdapter
from platform_core.adapters.deployment.ecs_adapter import ECSDeploymentAdapter
from platform_core.adapters.deployment.s3_adapter import S3FrontendDeploymentAdapter
from platform_core.adapters.infrastructure.terraform_adapter import TerraformInfrastructureAdapter
from platform_core.adapters.verification.health_verifier import SyntheticHealthVerifier
from platform_core.adapters.build.dockerfile_adapter import DockerfileBuildAdapter
from platform_core.adapters.build.node_adapter import NodeBuildAdapter


class TestAdapterPolymorphism(unittest.TestCase):

    def test_01_all_adapters_inherit_base_platform_adapter(self):
        adapters = [
            ECSDeploymentAdapter(),
            S3FrontendDeploymentAdapter(),
            TerraformInfrastructureAdapter(),
            SyntheticHealthVerifier(),
            DockerfileBuildAdapter(),
            NodeBuildAdapter()
        ]
        for adapter in adapters:
            self.assertIsInstance(
                adapter,
                BasePlatformAdapter,
                f"{adapter.__class__.__name__} must inherit from BasePlatformAdapter"
            )
            self.assertIsInstance(
                adapter,
                BaseAdapter,
                f"{adapter.__class__.__name__} must inherit from BaseAdapter"
            )

    def test_02_adapter_request_response_models(self):
        req = AdapterRequest(
            action="verify",
            target="backend",
            parameters={"timeout": 30},
            context={"env": "local"}
        )
        self.assertEqual(req.action, "verify")
        self.assertEqual(req.target, "backend")

        res = AdapterResult(
            adapter_name="test_adapter",
            success=True,
            data={"status": "ok"},
            execution_time_seconds=1.23
        )
        self.assertTrue(res.success)
        self.assertEqual(res.adapter_name, "test_adapter")

    def test_03_lifecycle_methods_presence(self):
        class DummyAdapter(BasePlatformAdapter):
            def validate_prerequisites(self, context):
                return True
            def execute(self, request):
                return AdapterResult(adapter_name=self.adapter_name, success=True)

        dummy = DummyAdapter(adapter_name="dummy", version="2.0.0")
        self.assertTrue(dummy.validate_prerequisites({}))
        res = dummy.execute(AdapterRequest(action="test", target="none"))
        self.assertTrue(res.success)
        # Verify cleanup is callable
        dummy.cleanup()


if __name__ == "__main__":
    unittest.main()
