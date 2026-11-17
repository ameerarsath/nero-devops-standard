"""
NERO Universal Enterprise DevOps Automation Platform
Unit Tests for Pipeline Parameter Injection Defense (A1-JNK-002)

Verifies regex defense blocking shell metacharacters in CI/CD pipeline input parameters.
"""

import re
import unittest

SAFE_PARAM_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\.:]+$')


class TestPipelineParameterDefense(unittest.TestCase):

    def test_01_valid_parameters_accepted(self):
        valid_cases = [
            "hotel-billing",
            "sample-node-service",
            "sample-python-worker",
            "develop",
            "qa",
            "prod",
            "floci",
            "floci-local",
            "aws",
            "multi_account",
            "single_account",
            "rel-20261108120000",
            "v1.0.0",
            "localhost:5100"
        ]
        for val in valid_cases:
            self.assertTrue(
                bool(SAFE_PARAM_PATTERN.match(val)),
                f"Valid parameter '{val}' should be accepted"
            )

    def test_02_shell_injection_metacharacters_rejected(self):
        malicious_cases = [
            "hotel-billing; rm -rf /",
            "develop && echo hacked",
            "qa | cat /etc/passwd",
            "prod `whoami`",
            "$(id)",
            "floci & disown",
            "rel-01\nrm -rf *",
            "app>out.txt",
            "app<in.txt",
            "app' OR '1'='1"
        ]
        for val in malicious_cases:
            self.assertFalse(
                bool(SAFE_PARAM_PATTERN.match(val)),
                f"Malicious parameter '{val}' must be rejected by parameter defense regex"
            )


if __name__ == "__main__":
    unittest.main()
