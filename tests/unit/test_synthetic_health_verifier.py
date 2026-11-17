"""
NERO Platform - Synthetic Health Verification Adapter Tests (A1-TST-002)
Tests configurable polling thresholds, backoff, transient error recovery, and strict HTTP 200 enforcement.
"""

import unittest
from unittest.mock import patch, MagicMock
import urllib.error

from platform_core.adapters.verification.health_verifier import HealthVerificationAdapter, CheckStatus
from platform_core.engine.resolver import resolve_environment_context
from platform_core.engine.errors import PlatformError, DeploymentVerificationError


class TestSyntheticHealthVerifier(unittest.TestCase):

    def setUp(self):
        self.context = resolve_environment_context(
            app_id="hotel-billing",
            environment="develop",
            target_platform="floci",
            in_docker=False
        )
        self.adapter = HealthVerificationAdapter(
            default_max_attempts=3,
            default_retry_delay=0.01,
            default_timeout=1.0,
            default_backoff_factor=1.5
        )

    def test_configurable_defaults(self):
        """Verifies configurable retry and threshold parameters."""
        custom_adapter = HealthVerificationAdapter(
            default_max_attempts=10,
            default_retry_delay=0.5,
            default_timeout=2.0,
            default_backoff_factor=2.0
        )
        self.assertEqual(custom_adapter.default_max_attempts, 10)
        self.assertEqual(custom_adapter.default_retry_delay, 0.5)
        self.assertEqual(custom_adapter.default_timeout, 2.0)
        self.assertEqual(custom_adapter.default_backoff_factor, 2.0)

    @patch("time.sleep", return_value=None)
    @patch("urllib.request.urlopen")
    def test_transient_failure_recovery(self, mock_urlopen, mock_sleep):
        """Verifies polling recovers gracefully when backend responds after transient connection errors."""
        # Fail first 2 attempts with URLError (connection refused), succeed on 3rd attempt with HTTP 200
        mock_success = MagicMock()
        mock_success.status = 200

        mock_urlopen.side_effect = [
            urllib.error.URLError("Connection refused"),
            urllib.error.URLError("Connection reset"),
            mock_success
        ]

        report = self.adapter.verify(
            self.context,
            s3_bucket=None,
            ecs_host="localhost",
            max_attempts=5,
            retry_delay_seconds=0.01
        )

        self.assertTrue(report.all_passed)
        self.assertEqual(len(report.checks), 1)
        self.assertEqual(report.checks[0].status, CheckStatus.PASSED)
        self.assertEqual(report.checks[0].actual_status, 200)
        self.assertGreaterEqual(mock_urlopen.call_count, 3)

    @patch("time.sleep", return_value=None)
    @patch("urllib.request.urlopen")
    def test_strict_http_401_403_rejection(self, mock_urlopen, mock_sleep):
        """Verifies health check strictly rejects HTTP 401/403 as authorization policy failure."""
        mock_http_err = urllib.error.HTTPError(
            url="http://localhost:8080/health",
            code=403,
            msg="Forbidden",
            hdrs={},
            fp=None
        )
        mock_urlopen.side_effect = mock_http_err

        with self.assertRaises(PlatformError):
            self.adapter.verify(
                self.context,
                s3_bucket=None,
                ecs_host="localhost",
                max_attempts=2,
                retry_delay_seconds=0.01
            )

    @patch("time.sleep", return_value=None)
    @patch("urllib.request.urlopen")
    def test_retry_exhaustion_fails_closed(self, mock_urlopen, mock_sleep):
        """Verifies that exceeding max_attempts raises PlatformError with check details."""
        mock_urlopen.side_effect = urllib.error.URLError("Target host unreachable")

        with self.assertRaises(PlatformError) as ctx:
            self.adapter.verify(
                self.context,
                s3_bucket=None,
                ecs_host="localhost",
                max_attempts=3,
                retry_delay_seconds=0.01
            )
        self.assertIn("health checks failed", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
