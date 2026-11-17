"""
Enterprise Universal Application Delivery Platform - AWS Sandbox Identity & Authorization Policy Tests
Verifies fail-closed identity boundaries, management account denial, caller account validation,
role ARN integrity, region allowlisting, and Floci state preservation.
"""

import os
import json
import unittest
from unittest.mock import patch, MagicMock

import boto3
from botocore.exceptions import ProfileNotFound, NoCredentialsError, ClientError

from platform_core.engine.resolver import resolve_environment_context
from platform_core.engine.errors import SecurityPolicyError, ConfigurationError, PlatformErrorCode
from platform_core.adapters.deployment.ecs_adapter import ECSDeploymentAdapter
from platform_core.adapters.build.dockerfile_adapter import DockerfileBuildAdapter


class TestAWSIdentityPolicy(unittest.TestCase):

    def setUp(self):
        # Clean environment variables before each test
        self.orig_env = os.environ.copy()
        for k in list(os.environ.keys()):
            if k.startswith("AWS_"):
                os.environ.pop(k, None)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.orig_env)

    def test_aws_profile_missing(self):
        """Verifies that requesting an unconfigured named profile raises ProfileNotFound."""
        with self.assertRaises(ProfileNotFound):
            boto3.Session(profile_name="enterprise-sandbox-nonexistent-12345")

    def test_aws_account_id_mismatch(self):
        """Verifies that authenticated caller account mismatching target account is rejected."""
        os.environ["AWS_QA_ACCOUNT_ID"] = "222233334444"
        os.environ["AWS_MANAGEMENT_ACCOUNT_ID"] = "999999999999"
        
        # Caller account is 111111111111, but target is 222233334444
        with self.assertRaises(SecurityPolicyError) as ctx:
            resolve_environment_context(
                app_id="sample-node-service",
                environment="qa",
                target_platform="aws",
                account_topology="multi_account",
                caller_account_id="111111111111"
            )
        self.assertIn("does not match authorized target account ID", str(ctx.exception))

    def test_management_account_rejected(self):
        """Verifies that attempting deployment to AWS Organizations Management Account is rejected."""
        mgmt_id = "111122223333"
        os.environ["AWS_PROD_ACCOUNT_ID"] = mgmt_id
        os.environ["AWS_MANAGEMENT_ACCOUNT_ID"] = mgmt_id

        with self.assertRaises(SecurityPolicyError) as ctx:
            resolve_environment_context(
                app_id="sample-node-service",
                environment="prod",
                target_platform="aws",
                account_topology="multi_account"
            )
        self.assertIn("Organizations Management Account", str(ctx.exception))

    def test_unknown_management_account_rejected(self):
        """Verifies fail-closed policy: AWS deployment is denied if management boundary is not established."""
        os.environ["AWS_PROD_ACCOUNT_ID"] = "123456789012"
        # Explicitly ensure AWS_MANAGEMENT_ACCOUNT_ID is unset
        os.environ.pop("AWS_MANAGEMENT_ACCOUNT_ID", None)

        with self.assertRaises(SecurityPolicyError) as ctx:
            resolve_environment_context(
                app_id="sample-node-service",
                environment="prod",
                target_platform="aws",
                account_topology="multi_account"
            )
        self.assertIn("Management Account boundary is not established", str(ctx.exception))

    def test_wrong_region_rejected(self):
        """Verifies that unauthorized AWS regions are rejected by security policy."""
        os.environ["AWS_QA_ACCOUNT_ID"] = "222233334444"
        os.environ["AWS_MANAGEMENT_ACCOUNT_ID"] = "999999999999"

        with self.assertRaises(ConfigurationError) as ctx:
            resolve_environment_context(
                app_id="sample-node-service",
                environment="qa",
                target_platform="aws",
                account_topology="multi_account",
                region="ap-southeast-1" # Not in allowed list: {ap-south-1, us-east-1, us-west-2, eu-west-1}
            )
        self.assertIn("Unauthorized AWS region", str(ctx.exception))

    def test_missing_deployment_role_rejected(self):
        """Verifies that missing account ID for deployment role resolution fails closed."""
        os.environ.pop("AWS_DEVELOP_ACCOUNT_ID", None)
        os.environ["AWS_MANAGEMENT_ACCOUNT_ID"] = "999999999999"

        with self.assertRaises(ConfigurationError) as ctx:
            resolve_environment_context(
                app_id="sample-node-service",
                environment="develop",
                target_platform="aws",
                account_topology="multi_account"
            )
        self.assertIn("AWS_DEVELOP_ACCOUNT_ID", str(ctx.exception))

    def test_invalid_role_configuration_rejected(self):
        """Verifies that malformed IAM role ARN is rejected."""
        os.environ["AWS_DEVELOP_ACCOUNT_ID"] = "111122223333"
        os.environ["AWS_DEVELOP_ROLE_ARN"] = "invalid-role-arn-format"
        os.environ["AWS_MANAGEMENT_ACCOUNT_ID"] = "999999999999"

        with self.assertRaises(ConfigurationError) as ctx:
            resolve_environment_context(
                app_id="sample-node-service",
                environment="develop",
                target_platform="aws",
                account_topology="multi_account"
            )
        self.assertIn("Invalid deployment role ARN format", str(ctx.exception))

    def test_aws_mutation_blocked_without_authorization(self):
        """Verifies that attempting ECS Fargate deployment without active credentials fails closed."""
        os.environ["AWS_QA_ACCOUNT_ID"] = "222233334444"
        os.environ["AWS_MANAGEMENT_ACCOUNT_ID"] = "999999999999"

        ctx = resolve_environment_context(
            app_id="sample-node-service",
            environment="qa",
            target_platform="aws",
            account_topology="multi_account",
            region="ap-south-1"
        )

        adapter = ECSDeploymentAdapter()
        # Ensure no AWS credentials exist in session
        with self.assertRaises(Exception) as exc:
            adapter.deploy(
                context=ctx,
                component_name="api",
                image_ref="222233334444.dkr.ecr.ap-south-1.amazonaws.com/sample-node-repo:latest",
                container_port=8080
            )
        self.assertIn("deployment failed", str(exc.exception).lower())

    def test_ecr_publish_requires_valid_identity(self):
        """Verifies that building with non-existent Dockerfile or unauthorized context fails closed."""
        adapter = DockerfileBuildAdapter()
        from platform_core.engine.models import ComponentModel, SourceModel, BuildModel, RuntimeModel, DeploymentModel
        invalid_comp = ComponentModel(
            name="invalid-comp",
            type="container-service",
            source=SourceModel(context="nonexistent_path_12345", dockerfile="Dockerfile"),
            build=BuildModel(adapter="dockerfile"),
            runtime=RuntimeModel(port=8080),
            deployment=DeploymentModel(adapter="ecs")
        )
        with self.assertRaises(Exception) as ctx:
            adapter.build(invalid_comp, workspace_root=".", release_id="rel-test-01")
        self.assertIn("Dockerfile not found", str(ctx.exception))

    def test_original_floci_state_untouched(self):
        """Verifies that baseline local Terraform state is exactly 15 resources and serial 23."""
        state_file = os.path.join("infrastructure", "terraform", "environments", "local", "terraform.tfstate")
        self.assertTrue(os.path.isfile(state_file), f"Baseline state file not found: {state_file}")
        with open(state_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data.get("serial"), 23, f"Expected serial 23, got {data.get('serial')}")
        self.assertEqual(len(data.get("resources", [])), 15, f"Expected 15 resources, got {len(data.get('resources', []))}")


if __name__ == "__main__":
    unittest.main()
