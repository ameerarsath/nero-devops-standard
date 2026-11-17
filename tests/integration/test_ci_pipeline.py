"""
NERO Universal Enterprise DevOps Automation Platform
End-to-End CI Pipeline Qualification Test Suite (A3-EVN-003)

Qualifies the complete event-driven Continuous Integration workflow across
all four reference applications: hotel-billing, sample-node-service,
sample-python-worker, and sample-go-service.
"""

import hashlib
import hmac
import json
import os
import tempfile
import time
import pytest

from platform_core.adapters.scm.base import SCMPushEvent, SCMPullRequestEvent, SCMCommit, SCMEventType
from platform_core.adapters.scm.github_adapter import GitHubAdapter
from platform_core.ci.idempotency_engine import IdempotencyEngine
from platform_core.ci.pr_validator import PRValidator
from platform_core.ci.jenkins_trigger import JenkinsTriggerBridge
from platform_core.ci.feedback_publisher import FeedbackPublisher
from platform_core.ci.webhook_gateway import create_default_ci_event_handler
from platform_core.engine.build_orchestrator import BuildOrchestrator
from platform_core.engine.test_orchestrator import TestOrchestrator
from platform_core.adapters.security.scanner_orchestrator import SecurityScanOrchestrator
from platform_core.engine.ci_evidence import CIEvidenceGenerator
from platform_core.audit.audit_verifier import verify_audit_ledger


REFERENCE_APPLICATIONS = [
    {
        "id": "hotel-billing",
        "spec_path": "app.spec.yaml",
        "repo": "https://github.com/ameerarsath/billing-system.git",
        "branch": "develop",
        "commit": "a1b2c3d4e5f67890123456789abcdef012345678",
        "components": ["backend", "frontend"]
    },
    {
        "id": "sample-node-service",
        "spec_path": "applications/sample-node-service/app.spec.yaml",
        "repo": "https://github.com/nero-enterprise/sample-node-service.git",
        "branch": "develop",
        "commit": "b2c3d4e5f6a17890123456789abcdef012345678",
        "components": ["api"]
    },
    {
        "id": "sample-python-worker",
        "spec_path": "applications/sample-python-worker/app.spec.yaml",
        "repo": "https://github.com/nero-enterprise/sample-python-worker.git",
        "branch": "develop",
        "commit": "c3d4e5f6a1b27890123456789abcdef012345678",
        "components": ["worker"]
    },
    {
        "id": "sample-go-service",
        "spec_path": "applications/sample-go-service/app.spec.yaml",
        "repo": "https://github.com/nero-enterprise/sample-go-service.git",
        "branch": "develop",
        "commit": "d4e5f6a1b2c37890123456789abcdef012345678",
        "components": ["api"]
    },
]


@pytest.mark.parametrize("app", REFERENCE_APPLICATIONS)
def test_e2e_ci_workflow_reference_apps(app):
    """Verifies end-to-end CI pipeline execution for each reference application."""
    app_id = app["id"]
    spec_path = app["spec_path"]
    commit_sha = app["commit"]
    repo_url = app["repo"]

    # 1. Build Orchestration
    orchestrator = BuildOrchestrator()
    build_res = orchestrator.build_application(spec_path=spec_path, tag="ci-qual-01", dry_run=True)
    assert build_res.success is True
    assert build_res.application_id == app_id
    assert build_res.total_components == len(app["components"])

    # 2. Automated Testing
    test_runner = TestOrchestrator()
    test_res = test_runner.run_tests_for_application(spec_path=spec_path, dry_run=True)
    assert test_res.success is True
    assert test_res.total_tests > 0

    # 3. DevSecOps Security Scanning
    sec_scanner = SecurityScanOrchestrator()
    sec_res = sec_scanner.scan_all(target_path=os.path.dirname(spec_path) or ".")
    assert sec_res.blocking_findings == 0
    assert sec_res.passed is True

    # 4. PR Validation Check
    validator = PRValidator()
    pr_event = SCMPullRequestEvent(
        event_type=SCMEventType.PULL_REQUEST,
        delivery_id=f"deliv-e2e-{app_id}",
        provider="github",
        action="opened",
        pr_id="101",
        pr_title=f"feat({app_id}): continuous integration qualification",
        repository_url=repo_url,
        repository_name=f"nero-enterprise/{app_id}",
        source_branch=f"feature/{app_id}-ci",
        target_branch="develop",
        source_repo_url=repo_url,
        is_fork=False,
        head_commit=SCMCommit(
            sha=commit_sha,
            message=f"feat({app_id}): e2e qualification",
            author_name="NERO Lead Architect",
            author_email="architect@nero.local",
            timestamp="2026-11-08T15:00:00Z"
        ),
        sender="nero-architect"
    )

    pr_report = validator.validate_pull_request(pr_event, custom_spec_path=spec_path)
    assert pr_report.overall_passed is True
    assert pr_report.passed_steps >= 11

    # 5. SCM Feedback Publishing
    gh_adapter = GitHubAdapter()
    publisher = FeedbackPublisher(scm_adapter=gh_adapter)
    published_ok = publisher.publish_validation_report(
        report=pr_report,
        repo_url=repo_url,
        commit_sha=commit_sha,
        build_url=f"http://localhost:8080/job/universal-ci-pipeline/100"
    )
    assert published_ok is True
    assert len(gh_adapter.published_statuses) == 1
    assert len(gh_adapter.posted_comments) == 1

    # 6. CI Evidence Generation & Cryptographic Audit Append
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        evidence_file = tf.name

    try:
        ev_generator = CIEvidenceGenerator()
        record = ev_generator.generate_and_record(
            application_id=app_id,
            commit_sha=commit_sha,
            branch="develop",
            repository=repo_url,
            pull_request_id="101",
            build_number=100,
            build_result="SUCCESS",
            test_summary={
                "total": test_res.total_tests,
                "passed": test_res.passed,
                "failed": test_res.failed,
                "coverage_percentage": 85.0
            },
            security_summary={
                "secrets_detected": sec_res.secrets.findings_count,
                "sast_issues": sec_res.sast.error_count,
                "cve_critical": sec_res.sca.critical_count,
                "cve_high": sec_res.sca.high_count
            },
            artifacts=[
                {"component": c, "image": f"nero/{app_id}-{c}:ci-qual-01", "digest": f"sha256:{hash(c) & 0xffffffffffffffff:016x}"}
                for c in app["components"]
            ],
            output_file=evidence_file
        )

        assert record.application_id == app_id
        assert record.checksum is not None
        assert record.jenkins.result == "SUCCESS"
    finally:
        if os.path.exists(evidence_file):
            os.remove(evidence_file)


def test_audit_ledger_integrity_after_ci_qualifications():
    """Verifies that the entire cryptographic audit log remains 100% valid."""
    audit_file = "platform_core/audit/audit_log.jsonl"
    valid, msg, count = verify_audit_ledger(audit_file)
    assert valid is True
    assert int(count) >= 63
    print(f"Cryptographic Audit Ledger Validated: {count} chained records. Msg: {msg}")


def test_idempotent_event_handler_deduplication():
    """Verifies that the default CI handler rejects duplicate webhook deliveries."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    try:
        engine = IdempotencyEngine(db_path=db_path)
        bridge = JenkinsTriggerBridge(offline_mock=True)
        handler = create_default_ci_event_handler(idempotency_engine=engine, trigger_bridge=bridge)

        event = SCMPushEvent(
            event_type=SCMEventType.PUSH,
            delivery_id="delivery-dedup-001",
            provider="github",
            repository_url="https://github.com/nero-enterprise/hotel-billing.git",
            repository_name="nero-enterprise/hotel-billing",
            branch="develop",
            ref="refs/heads/develop",
            head_commit=SCMCommit(sha="sha-dedup-1", message="dedup test", author_name="Dev"),
            after_sha="sha-dedup-1",
            sender="dev"
        )

        # 1. First execution -> Triggered
        res1 = handler(event)
        assert res1["status"] == "TRIGGERED"

        # 2. Second delivery with same delivery ID -> Deduped
        res2 = handler(event)
        assert res2["status"] == "ALREADY_COMPLETED"
        assert res2["cached_response"] is not None
        assert res2["cached_response"]["status"] == "TRIGGERED"
    finally:
        import gc
        gc.collect()
        time.sleep(0.1)
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception:
                pass
