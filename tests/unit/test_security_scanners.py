"""
NERO Universal Enterprise DevOps Automation Platform
Unit Tests for DevSecOps Security Scanners (A3-SEC-001 - A3-SEC-004)
"""

import datetime
import os
import tempfile
import yaml
import pytest

from platform_core.adapters.security.gitleaks_adapter import GitleaksAdapter
from platform_core.adapters.security.semgrep_adapter import SemgrepAdapter
from platform_core.adapters.security.trivy_adapter import TrivyAdapter
from platform_core.adapters.security.scanner_orchestrator import SecurityScanOrchestrator
from platform_core.policy.security_exceptions import SecurityExceptionsEngine, SecurityExceptionRule


def test_gitleaks_secret_detection_and_masking():
    with tempfile.TemporaryDirectory() as temp_dir:
        # 1. Create file with mock exposed AWS key
        bad_file = os.path.join(temp_dir, "credentials.txt")
        with open(bad_file, "w") as f:
            f.write("AWS_ACCESS_KEY_ID = 'AKIAIOSFODNN7EXAMPLE'\n")

        adapter = GitleaksAdapter()
        res = adapter.scan_repository(repo_path=temp_dir)

        assert res.passed is False
        assert res.findings_count >= 1
        assert res.findings[0].masked_value == "****[REDACTED]****"
        assert "AKIAIOSFODNN7EXAMPLE" not in res.findings[0].masked_value

        # 2. Clean directory
        os.remove(bad_file)
        good_file = os.path.join(temp_dir, "clean.py")
        with open(good_file, "w") as f:
            f.write("print('Hello secure world')\n")

        res_clean = adapter.scan_repository(repo_path=temp_dir)
        assert res_clean.passed is True
        assert res_clean.findings_count == 0


def test_semgrep_sast_pattern_detection():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create file with insecure shell=True
        vulnerable_py = os.path.join(temp_dir, "exec_tool.py")
        with open(vulnerable_py, "w") as f:
            f.write("import subprocess\nsubprocess.Popen('ls ' + user_input, shell=True)\n")

        adapter = SemgrepAdapter()
        res = adapter.scan_repository(repo_path=temp_dir)

        assert res.passed is False
        assert res.error_count >= 1
        assert any(f.rule_id == "nero-sast-insecure-subprocess-shell-true" for f in res.findings)


def test_trivy_sca_lockfile_scanning():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create lockfile with vulnerable log4j dependency
        pom_file = os.path.join(temp_dir, "pom.xml")
        with open(pom_file, "w") as f:
            f.write("<project><dependencies><dependency><artifactId>log4j-core</artifactId><version>2.14.1</version></dependency></dependencies></project>")

        adapter = TrivyAdapter()
        res = adapter.scan_dependencies(target_path=temp_dir)

        assert res.passed is False
        assert res.critical_count >= 1
        assert any(f.cve_id == "CVE-2021-44228" for f in res.findings)
        assert res.vulnerability_db_version != ""
        assert res.vulnerability_db_age_days == 0


def test_security_exceptions_engine_active_and_expired():
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w") as tf:
        now = datetime.datetime.now(datetime.timezone.utc)
        future = (now + datetime.timedelta(days=30)).isoformat()
        past = (now - datetime.timedelta(days=10)).isoformat()

        config = {
            "version": "1.0.0",
            "exceptions": [
                {
                    "id": "EXC-VALID-01",
                    "finding_id": "CVE-2021-44228",
                    "target": "pom.xml",
                    "justification": "Approved isolation for local Floci integration tests only",
                    "approver": "security-architect@nero.local",
                    "created_at": now.isoformat(),
                    "expires_at": future,
                    "revoked": False
                },
                {
                    "id": "EXC-EXPIRED-02",
                    "finding_id": "CVE-2022-23529",
                    "target": "package-lock.json",
                    "justification": "Expired exemption that must fail closed immediately",
                    "approver": "sec-ops@nero.local",
                    "created_at": past,
                    "expires_at": past,
                    "revoked": False
                }
            ]
        }
        yaml.dump(config, tf)
        config_path = tf.name

    try:
        engine = SecurityExceptionsEngine(exception_file=config_path)

        # 1. Valid active exemption
        exempted, rule_id = engine.is_exempted("CVE-2021-44228", "backend/pom.xml")
        assert exempted is True
        assert rule_id == "EXC-VALID-01"

        # 2. Expired exemption fails closed
        exempted_exp, reason = engine.is_exempted("CVE-2022-23529", "frontend/package-lock.json")
        assert exempted_exp is False
        assert "EXPIRED" in reason

        # 3. Non-existent rule fails closed
        exempted_none, _ = engine.is_exempted("CVE-RANDOM-99999", "pom.xml")
        assert exempted_none is False
    finally:
        if os.path.exists(config_path):
            os.remove(config_path)
