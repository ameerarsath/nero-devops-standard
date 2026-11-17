"""
NERO Universal Enterprise DevOps Automation Platform
Automated Tests for Deterministic Exit Codes (A1-FND-002)

Asserts that all platform failure modes return their assigned integer exit codes:
- SpecValidationError = 10
- CatalogAuthorizationError = 15
- SecurityPolicyError = 20
- InfrastructureError = 30
- DeploymentError = 40
- DeploymentVerificationError = 50
- GovernancePolicyError = 60
- ConfigurationError = 1
"""

import sys
import unittest
import subprocess
from pathlib import Path

from platform_core.engine.errors import (
    PlatformException,
    ConfigurationError,
    SpecValidationError,
    CatalogAuthorizationError,
    SecurityPolicyError,
    InfrastructureError,
    DeploymentError,
    DeploymentVerificationError,
    GovernancePolicyError,
    EXIT_CODE_SUCCESS,
    EXIT_CODE_GENERAL_ERROR,
    EXIT_CODE_SPEC_ERROR,
    EXIT_CODE_CATALOG_ERROR,
    EXIT_CODE_POLICY_ERROR,
    EXIT_CODE_INFRA_ERROR,
    EXIT_CODE_DEPLOY_ERROR,
    EXIT_CODE_VERIFY_ERROR,
    EXIT_CODE_GOVERNANCE_ERROR,
)


class TestDeterministicExitCodes(unittest.TestCase):

    def test_01_exit_code_constants(self):
        self.assertEqual(EXIT_CODE_SUCCESS, 0)
        self.assertEqual(EXIT_CODE_GENERAL_ERROR, 1)
        self.assertEqual(EXIT_CODE_SPEC_ERROR, 10)
        self.assertEqual(EXIT_CODE_CATALOG_ERROR, 15)
        self.assertEqual(EXIT_CODE_POLICY_ERROR, 20)
        self.assertEqual(EXIT_CODE_INFRA_ERROR, 30)
        self.assertEqual(EXIT_CODE_DEPLOY_ERROR, 40)
        self.assertEqual(EXIT_CODE_VERIFY_ERROR, 50)
        self.assertEqual(EXIT_CODE_GOVERNANCE_ERROR, 60)

    def test_02_exception_exit_code_attributes(self):
        self.assertEqual(SpecValidationError("invalid spec").exit_code, 10)
        self.assertEqual(CatalogAuthorizationError("unauthorized app").exit_code, 15)
        self.assertEqual(SecurityPolicyError("security breach").exit_code, 20)
        self.assertEqual(InfrastructureError("terraform failure").exit_code, 30)
        self.assertEqual(DeploymentError("container failed").exit_code, 40)
        self.assertEqual(DeploymentVerificationError("health probe failed").exit_code, 50)
        self.assertEqual(GovernancePolicyError("missing approval").exit_code, 60)
        self.assertEqual(ConfigurationError("bad config").exit_code, 1)

    def test_03_cli_spec_validation_failure_exit_code_10(self):
        cmd = [sys.executable, "-m", "platform_core.engine.cli", "validate", "--spec", "non_existent_file.yaml"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 10, f"Expected exit code 10, got {res.returncode}: {res.stderr}")

    def test_04_cli_catalog_failure_exit_code_15(self):
        cmd = [
            sys.executable, "-m", "platform_core.engine.cli", "check-catalog",
            "--app", "unregistered-app-xyz",
            "--env", "develop"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 15, f"Expected exit code 15, got {res.returncode}: {res.stderr}")


if __name__ == "__main__":
    unittest.main()
