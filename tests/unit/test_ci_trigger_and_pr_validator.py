"""
NERO Universal Enterprise DevOps Automation Platform
Unit Tests for CI Trigger Engine & PR Validator (A3-TRG-001 - A3-TRG-004)
"""

import os
import tempfile
import pytest

from platform_core.adapters.scm.base import (
    SCMPullRequestEvent,
    SCMCommit,
    SCMEventType,
)
from platform_core.adapters.scm.github_adapter import GitHubAdapter
from platform_core.ci.idempotency_engine import IdempotencyEngine
from platform_core.ci.pr_validator import PRValidator
from platform_core.ci.jenkins_trigger import JenkinsTriggerBridge
from platform_core.ci.feedback_publisher import FeedbackPublisher


def test_idempotency_engine_deduplication_and_persistence():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    try:
        engine1 = IdempotencyEngine(db_path=db_path)

        # 1. First event reservation
        deliv_id = "uuid-test-001"
        key = "repo:commit1:push"
        reserved, status, payload = engine1.check_and_reserve(deliv_id, key, "github", ttl_seconds=60)
        assert reserved is True
        assert status == "RESERVED"
        assert payload is None

        # 2. Duplicate while processing
        reserved2, status2, payload2 = engine1.check_and_reserve(deliv_id, key, "github", ttl_seconds=60)
        assert reserved2 is False
        assert status2 == "ALREADY_PROCESSING"

        # 3. Mark completed
        engine1.mark_completed(deliv_id, {"build_id": 42, "result": "SUCCESS"})

        # 4. Simulate process restart by creating new engine instance on same DB file
        engine2 = IdempotencyEngine(db_path=db_path)
        reserved3, status3, payload3 = engine2.check_and_reserve(deliv_id, key, "github", ttl_seconds=60)
        assert reserved3 is False
        assert status3 == "ALREADY_COMPLETED"
        assert payload3 is not None
        assert payload3["build_id"] == 42
    finally:
        import gc, time
        gc.collect()
        time.sleep(0.1)
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception:
                pass


def test_pr_validator_12_steps_qualified_app():
    validator = PRValidator()

    # Create mock valid PR event for hotel-billing
    event = SCMPullRequestEvent(
        event_type=SCMEventType.PULL_REQUEST,
        delivery_id="deliv-pr-100",
        provider="github",
        action="opened",
        pr_id="100",
        pr_title="feat: add new order checkout workflow",
        repository_url="https://github.com/nero-enterprise/hotel-billing.git",
        repository_name="nero-enterprise/hotel-billing",
        source_branch="feature/checkout",
        target_branch="develop",
        source_repo_url="https://github.com/nero-enterprise/hotel-billing.git",
        is_fork=False,
        head_commit=SCMCommit(
            sha="abcdef1234567890abcdef1234567890abcdef12",
            message="feat(checkout): add payment splitting",
            author_name="Alice Platform",
            author_email="alice@nero.local",
            timestamp="2026-11-08T14:00:00Z"
        ),
        sender="alice"
    )

    report = validator.validate_pull_request(event, repo_root=os.getcwd())
    assert report.total_steps == 12
    assert report.passed_steps >= 11  # All core checks pass on the workspace
    assert len(report.steps) == 12
    assert report.steps[0].step_name == "Catalog Authorization"
    assert report.steps[0].passed is True
    assert report.steps[1].step_name == "Branch Protection"
    assert report.steps[1].passed is True


def test_pr_validator_unauthorized_repository():
    validator = PRValidator()

    event = SCMPullRequestEvent(
        event_type=SCMEventType.PULL_REQUEST,
        delivery_id="deliv-pr-malicious",
        provider="github",
        action="opened",
        pr_id="666",
        pr_title="malicious: cryptominer injection",
        repository_url="https://github.com/attacker/rogue-repo.git",
        repository_name="attacker/rogue-repo",
        source_branch="master",
        target_branch="unauthorized-branch",
        source_repo_url="https://github.com/attacker/rogue-repo.git",
        is_fork=True,
        head_commit=SCMCommit(
            sha="badsha",
            message="hack",
            author_name="Attacker",
            author_email="attacker@darkweb.xyz",
            timestamp=""
        ),
        sender="attacker"
    )

    report = validator.validate_pull_request(event, repo_root=os.getcwd())
    assert report.overall_passed is False
    assert report.steps[0].passed is False  # Unauthorized repo
    assert report.steps[1].passed is False  # Unauthorized branch
    assert len(report.diagnostics) > 0


def test_jenkins_trigger_bridge_mock_and_params():
    bridge = JenkinsTriggerBridge(offline_mock=True)
    params = {
        "APPLICATION": "hotel-billing",
        "TARGET_ENV": "develop",
        "GIT_BRANCH": "develop",
        "COMMIT_SHA": "abcdef123456"
    }

    result = bridge.trigger_ci_pipeline("universal-ci-pipeline", params)
    assert result["success"] is True
    assert result["status"] == "QUEUED"
    assert result["job"] == "universal-ci-pipeline"
    assert result["parameters"]["APPLICATION"] == "hotel-billing"


def test_feedback_publisher_generates_markdown_and_status():
    adapter = GitHubAdapter()
    publisher = FeedbackPublisher(scm_adapter=adapter)

    # Validate PR
    validator = PRValidator()
    event = SCMPullRequestEvent(
        event_type=SCMEventType.PULL_REQUEST,
        delivery_id="deliv-pr-feedback",
        provider="github",
        action="synchronize",
        pr_id="77",
        pr_title="feat: split payment",
        repository_url="https://github.com/nero-enterprise/hotel-billing.git",
        repository_name="nero-enterprise/hotel-billing",
        source_branch="feature/split",
        target_branch="develop",
        source_repo_url="https://github.com/nero-enterprise/hotel-billing.git",
        is_fork=False,
        head_commit=SCMCommit(
            sha="1234567890abcdef",
            message="commit test",
            author_name="Tester",
            author_email="",
            timestamp=""
        ),
        sender="tester"
    )
    report = validator.validate_pull_request(event)

    ok = publisher.publish_validation_report(
        report=report,
        repo_url=event.repository_url,
        commit_sha=event.head_commit.sha,
        build_url="http://localhost:8080/job/universal-ci-pipeline/50"
    )

    assert ok is True
    assert len(adapter.published_statuses) == 1
    assert len(adapter.posted_comments) == 1
    comment_body = adapter.posted_comments[0]["body"]
    assert "NERO Continuous Integration Summary" in comment_body
    assert "Catalog Authorization" in comment_body
    assert "http://localhost:8080/job/universal-ci-pipeline/50" in comment_body
