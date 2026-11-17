"""
NERO Universal Enterprise DevOps Automation Platform
Unit Tests for AST Dockerfile Non-Root Enforcement Linter (A1-SEC-001)

Verifies programmatic enforcement of non-root container execution (fail-closed, exit code 20).
"""

import tempfile
import unittest
from pathlib import Path

from platform_core.policy.runtime_policy import (
    RuntimePolicyValidator,
    check_dockerfile_non_root
)
from platform_core.engine.errors import SecurityPolicyError, EXIT_CODE_POLICY_ERROR


class TestDockerfileSecurityLinter(unittest.TestCase):

    def test_01_valid_numeric_user_accepted(self):
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".Dockerfile") as f:
            f.write("FROM eclipse-temurin:17-jre\nUSER 10001\nCMD [\"java\", \"-jar\", \"app.jar\"]\n")
            f_path = Path(f.name)
        try:
            compliant, msg, user = check_dockerfile_non_root(f_path)
            self.assertTrue(compliant)
            self.assertEqual(user, "10001")
            # Must not raise
            RuntimePolicyValidator.enforce_non_root_policy(f_path, "backend")
        finally:
            f_path.unlink()

    def test_02_valid_named_user_accepted(self):
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".Dockerfile") as f:
            f.write("FROM node:22-alpine\nUSER node\nCMD [\"node\", \"server.js\"]\n")
            f_path = Path(f.name)
        try:
            compliant, msg, user = check_dockerfile_non_root(f_path)
            self.assertTrue(compliant)
            self.assertEqual(user, "node")
        finally:
            f_path.unlink()

    def test_03_missing_user_rejected(self):
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".Dockerfile") as f:
            f.write("FROM python:3.12-slim\nWORKDIR /app\nCMD [\"python\", \"worker.py\"]\n")
            f_path = Path(f.name)
        try:
            compliant, msg, user = check_dockerfile_non_root(f_path)
            self.assertFalse(compliant)
            self.assertIn("Missing explicit non-root USER", msg)
            with self.assertRaises(SecurityPolicyError) as ctx:
                RuntimePolicyValidator.enforce_non_root_policy(f_path, "worker")
            self.assertEqual(ctx.exception.exit_code, EXIT_CODE_POLICY_ERROR)
        finally:
            f_path.unlink()

    def test_04_explicit_root_user_rejected(self):
        for root_user in ["root", "0", "0:0"]:
            with tempfile.NamedTemporaryFile("w", delete=False, suffix=".Dockerfile") as f:
                f.write(f"FROM alpine:3.19\nUSER {root_user}\nCMD [\"sh\"]\n")
                f_path = Path(f.name)
            try:
                compliant, msg, user = check_dockerfile_non_root(f_path)
                self.assertFalse(compliant)
                self.assertIn("Prohibited root USER", msg)
                with self.assertRaises(SecurityPolicyError) as ctx:
                    RuntimePolicyValidator.enforce_non_root_policy(f_path, "test-comp")
                self.assertEqual(ctx.exception.exit_code, 20)
            finally:
                f_path.unlink()

    def test_05_multistage_final_stage_evaluated(self):
        # Stage 1 runs as root to install packages, Stage 2 drops privileges
        content = """
        FROM golang:1.22 AS builder
        WORKDIR /build
        RUN echo "build"

        FROM alpine:3.19
        WORKDIR /app
        USER 10001
        CMD ["./app"]
        """
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".Dockerfile") as f:
            f.write(content)
            f_path = Path(f.name)
        try:
            compliant, msg, user = check_dockerfile_non_root(f_path)
            self.assertTrue(compliant)
            self.assertEqual(user, "10001")
        finally:
            f_path.unlink()


if __name__ == "__main__":
    unittest.main()
