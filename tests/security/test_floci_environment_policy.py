"""
Enterprise Universal Application Delivery Platform - Floci Environment Policy Tests
Verifies Floci-first platform configuration, environment isolation, zero-AWS credential
requirements, fail-closed real-AWS gating, and Floci state preservation.
"""

import os
import json
import unittest
import boto3
from botocore.exceptions import ClientError

from platform_core.engine.platform_config import (
    load_platform_config,
    get_active_environment_config,
    PlatformConfigModel,
    EnvironmentConfigModel
)
from platform_core.engine.resolver import resolve_environment_context
from platform_core.engine.errors import SecurityPolicyError, ConfigurationError
from platform_core.adapters.deployment.ecs_adapter import ECSDeploymentAdapter


class TestFlociEnvironmentPolicy(unittest.TestCase):

    def setUp(self):
        self.orig_env = os.environ.copy()
        for k in list(os.environ.keys()):
            if k.startswith("AWS_"):
                os.environ.pop(k, None)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.orig_env)

    def test_platform_config_loads_and_validates(self):
        """Verifies platform_config.yaml loads with active floci-local environment."""
        cfg = load_platform_config("platform_config.yaml")
        self.assertEqual(cfg.deployment.active_environment, "floci-local")
        self.assertIn("floci-local", cfg.environments)
        self.assertIn("aws-production", cfg.environments)
        
        floci_env = cfg.environments["floci-local"]
        self.assertTrue(floci_env.enabled)
        self.assertEqual(floci_env.status, "ACTIVE")
        self.assertEqual(floci_env.type, "simulator")
        self.assertEqual(floci_env.region, "ap-south-1")
        self.assertEqual(floci_env.account_namespace, "000000000000")
        self.assertFalse(floci_env.allow_real_aws_fallback)

    def test_real_aws_environment_is_unconfigured(self):
        """Verifies aws-production environment is disabled and unconfigured by default."""
        cfg = load_platform_config("platform_config.yaml")
        aws_env = cfg.environments["aws-production"]
        self.assertFalse(aws_env.enabled)
        self.assertEqual(aws_env.status, "UNCONFIGURED")
        self.assertFalse(aws_env.allow_real_aws_fallback)

    def test_reject_silent_real_aws_fallback(self):
        """Verifies that setting allow_real_aws_fallback=True raises SecurityPolicyError."""
        with self.assertRaises(Exception) as ctx:
            EnvironmentConfigModel(
                type="simulator",
                endpoint="http://localhost:4566",
                region="ap-south-1",
                authentication="local-simulator",
                allow_real_aws_fallback=True
            )
        self.assertIn("Silent real-AWS fallback is strictly prohibited", str(ctx.exception))

    def test_floci_local_resolver_requires_no_aws_credentials(self):
        """Verifies resolving floci-local succeeds without any AWS credentials or profiles."""
        ctx = resolve_environment_context(
            app_id="sample-node-service",
            environment="qa",
            target_platform="floci-local",
            account_topology="multi_account",
            region="ap-south-1"
        )
        self.assertEqual(ctx.target_platform, "floci")
        self.assertEqual(ctx.account_id, "444455556666")
        self.assertEqual(ctx.region, "ap-south-1")
        self.assertIn("4566", ctx.floci_endpoint)
        self.assertIsNone(ctx.role_arn)

    def test_floci_single_account_resolves_000000000000(self):
        """Verifies single-account topology resolves to verified 000000000000 namespace."""
        ctx = resolve_environment_context(
            app_id="sample-node-service",
            environment="develop",
            target_platform="floci-local",
            account_topology="single_account",
            region="ap-south-1"
        )
        self.assertEqual(ctx.account_id, "000000000000")
        self.assertEqual(ctx.secret_name, "sample-node-service/develop/app-secrets")

    def test_real_aws_blocked_when_unconfigured(self):
        """Verifies attempting to deploy to real AWS is blocked when aws-production is unconfigured."""
        with self.assertRaises(SecurityPolicyError) as ctx:
            resolve_environment_context(
                app_id="sample-node-service",
                environment="qa",
                target_platform="aws",
                account_topology="multi_account"
            )
        self.assertIn("Real AWS deployment target is marked 'UNCONFIGURED'", str(ctx.exception))

    def test_floci_live_sts_connectivity(self):
        """Verifies live Boto3 STS connectivity against local Floci endpoint."""
        client = boto3.client(
            "sts",
            endpoint_url="http://localhost:4566",
            region_name="ap-south-1",
            aws_access_key_id="test",
            aws_secret_access_key="test"
        )
        ident = client.get_caller_identity()
        self.assertEqual(ident.get("Account"), "000000000000")
        self.assertEqual(ident.get("Arn"), "arn:aws:iam::000000000000:root")
        self.assertEqual(ident.get("UserId"), "000000000000")

    def test_floci_live_s3_connectivity(self):
        """Verifies live Boto3 S3 connectivity against local Floci endpoint."""
        client = boto3.client(
            "s3",
            endpoint_url="http://localhost:4566",
            region_name="ap-south-1",
            aws_access_key_id="test",
            aws_secret_access_key="test"
        )
        res = client.list_buckets()
        self.assertIn("Buckets", res)

    def test_original_floci_state_untouched(self):
        """Verifies baseline local Terraform state remains untouched at Serial 23 and 15 resources."""
        state_file = os.path.join("infrastructure", "terraform", "environments", "local", "terraform.tfstate")
        self.assertTrue(os.path.isfile(state_file), f"Baseline state file not found: {state_file}")
        with open(state_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data.get("serial"), 23, f"Expected serial 23, got {data.get('serial')}")
        self.assertEqual(len(data.get("resources", [])), 15, f"Expected 15 resources, got {len(data.get('resources', []))}")


if __name__ == "__main__":
    unittest.main()
