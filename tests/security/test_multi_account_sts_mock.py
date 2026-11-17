"""
NERO Platform - Multi-Account AWS STS Mock Fixture Tests (A1-TST-003)
Tests STS AssumeRole simulation, management account denial, session naming, and credential validity.
"""

import unittest
from botocore.exceptions import ClientError

from tests.fixtures.sts_mock import (
    MockSTSClient,
    MANAGEMENT_ACCOUNT_ID,
    DEVELOP_ACCOUNT_ID,
    QA_ACCOUNT_ID,
    PROD_ACCOUNT_ID,
    CALLER_IDENTITY_ACCOUNT_ID
)
from platform_core.engine.resolver import resolve_environment_context


class TestMultiAccountSTSMock(unittest.TestCase):

    def setUp(self):
        self.sts = MockSTSClient(
            caller_account_id=CALLER_IDENTITY_ACCOUNT_ID,
            management_account_id=MANAGEMENT_ACCOUNT_ID
        )

    def test_caller_identity_verification(self):
        """Verifies mock caller identity matches expected bootstrap account."""
        identity = self.sts.get_caller_identity()
        self.assertEqual(identity["Account"], CALLER_IDENTITY_ACCOUNT_ID)
        self.assertIn(CALLER_IDENTITY_ACCOUNT_ID, identity["Arn"])

    def test_assume_role_success_target_environments(self):
        """Verifies AssumeRole produces valid temporary credentials for member accounts."""
        target_accounts = [
            ("develop", DEVELOP_ACCOUNT_ID),
            ("qa", QA_ACCOUNT_ID),
            ("prod", PROD_ACCOUNT_ID)
        ]

        for env, acc_id in target_accounts:
            role_arn = f"arn:aws:iam::{acc_id}:role/NERODeploymentRole"
            session_name = f"nero-deploy-{env}-session"
            response = self.sts.assume_role(RoleArn=role_arn, RoleSessionName=session_name)

            self.assertIn("Credentials", response)
            creds = response["Credentials"]
            self.assertTrue(creds["AccessKeyId"].startswith("ASIA"))
            self.assertTrue(len(creds["SecretAccessKey"]) > 20)
            self.assertTrue(len(creds["SessionToken"]) > 20)
            self.assertIn(acc_id, response["AssumedRoleUser"]["Arn"])
            self.assertIn(session_name, response["AssumedRoleUser"]["Arn"])

    def test_management_account_assume_role_denied(self):
        """Verifies fail-closed policy: targeting the Organizations Management Account is rejected."""
        mgmt_role_arn = f"arn:aws:iam::{MANAGEMENT_ACCOUNT_ID}:role/OrganizationAdminRole"
        session_name = "attempt-mgmt-deployment"

        with self.assertRaises(ClientError) as ctx:
            self.sts.assume_role(RoleArn=mgmt_role_arn, RoleSessionName=session_name)

        err = ctx.exception.response["Error"]
        self.assertEqual(err["Code"], "AccessDenied")
        self.assertIn("Management Account", err["Message"])

    def test_malformed_role_arn_rejected(self):
        """Verifies that invalid role ARN formats are rejected with ValidationError."""
        invalid_arns = [
            "invalid-arn-string",
            "arn:aws:s3:::my-bucket",
            "arn:aws:iam::123:role/ShortAccount",
            "arn:aws:iam::abcdefghijkl:role/NonNumericAccount"
        ]

        for bad_arn in invalid_arns:
            with self.assertRaises(ClientError) as ctx:
                self.sts.assume_role(RoleArn=bad_arn, RoleSessionName="test-session")
            self.assertEqual(ctx.exception.response["Error"]["Code"], "ValidationError")

    def test_malformed_session_name_rejected(self):
        """Verifies that session names with invalid characters are rejected."""
        role_arn = f"arn:aws:iam::{DEVELOP_ACCOUNT_ID}:role/ValidRole"
        invalid_sessions = [
            "s",  # too short (< 2)
            "session with spaces",
            "session;inject_cmd",
            "session$bad*chars",
            "a" * 65  # too long (> 64)
        ]

        for bad_session in invalid_sessions:
            with self.assertRaises(ClientError) as ctx:
                self.sts.assume_role(RoleArn=role_arn, RoleSessionName=bad_session)
            self.assertEqual(ctx.exception.response["Error"]["Code"], "ValidationError")


if __name__ == "__main__":
    unittest.main()
