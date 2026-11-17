"""
NERO Universal Enterprise DevOps Automation Platform
Unit Tests for Secret Masking and Log Redaction (A1-SEC-002)
"""

import io
import unittest
from platform_core.engine.cli import SecretScrubber


class TestSecretScrubber(unittest.TestCase):

    def setUp(self):
        self.buffer = io.StringIO()
        self.scrubber = SecretScrubber(self.buffer)

    def test_01_scrub_jwt_token(self):
        sample_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        msg = f"User logged in with token {sample_jwt}"
        self.scrubber.write(msg)
        output = self.buffer.getvalue()
        self.assertNotIn(sample_jwt, output)
        self.assertIn("****[REDACTED_JWT]****", output)

    def test_02_scrub_password_and_secret(self):
        msg = "DATABASE_URL=postgres://admin:SuperSecret123!@localhost:5432/db with JWT_SECRET='ultra-secure-key-999'"
        self.scrubber.write(msg)
        output = self.buffer.getvalue()
        self.assertNotIn("SuperSecret123!", output)
        self.assertNotIn("ultra-secure-key-999", output)
        self.assertIn("****[REDACTED]****", output)

    def test_03_innocuous_strings_pass_through(self):
        msg = "Application hotel-billing deployed successfully to develop on floci."
        self.scrubber.write(msg)
        output = self.buffer.getvalue()
        self.assertEqual(output, msg)


if __name__ == "__main__":
    unittest.main()
