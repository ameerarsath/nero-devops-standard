"""
NERO Universal Enterprise DevOps Automation Platform
Unit Tests for SCM Adapters (A3-SCM-001, A3-SCM-002, A3-SCM-003)
"""

import hashlib
import hmac
import json
import pytest

from platform_core.adapters.scm.base import (
    SCMEventType,
    SCMStatusUpdate,
    SCMStatusState,
    SCMComment,
)
from platform_core.adapters.scm.github_adapter import GitHubAdapter
from platform_core.adapters.scm.bitbucket_adapter import BitbucketAdapter
from platform_core.adapters.scm.gitlab_adapter import GitLabAdapter


def test_github_adapter_signature_verification():
    adapter = GitHubAdapter()
    secret = "my-secret-webhook-key"
    payload = b'{"ref": "refs/heads/main", "after": "abc1234"}'

    # Compute valid HMAC-SHA256
    valid_sig = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

    # Valid verification
    assert adapter.verify_webhook({"X-Hub-Signature-256": valid_sig}, payload, secret) is True

    # Tampered payload
    tampered_payload = b'{"ref": "refs/heads/main", "after": "tampered"}'
    assert adapter.verify_webhook({"X-Hub-Signature-256": valid_sig}, tampered_payload, secret) is False

    # Invalid secret
    assert adapter.verify_webhook({"X-Hub-Signature-256": valid_sig}, payload, "wrong-secret") is False

    # Missing header
    assert adapter.verify_webhook({}, payload, secret) is False

    # Invalid header format
    assert adapter.verify_webhook({"X-Hub-Signature-256": "invalid-format"}, payload, secret) is False


def test_github_adapter_push_event_normalization():
    adapter = GitHubAdapter()
    payload = {
        "ref": "refs/heads/develop",
        "before": "0000000000000000000000000000000000000000",
        "after": "c0ffee1234567890abcdef1234567890abcdef12",
        "repository": {
            "full_name": "nero-enterprise/hotel-billing",
            "clone_url": "https://github.com/nero-enterprise/hotel-billing.git"
        },
        "head_commit": {
            "id": "c0ffee1234567890abcdef1234567890abcdef12",
            "message": "feat(api): add new billing invoice endpoint",
            "author": {
                "name": "Jane Developer",
                "email": "jane@nero.local"
            },
            "timestamp": "2026-11-08T10:00:00Z"
        },
        "sender": {"login": "janedev"}
    }
    payload_bytes = json.dumps(payload).encode()
    headers = {
        "X-GitHub-Event": "push",
        "X-GitHub-Delivery": "delivery-uuid-9988"
    }

    event = adapter.parse_webhook_event(headers, payload_bytes)
    assert event is not None
    assert event.event_type == SCMEventType.PUSH
    assert event.provider == "github"
    assert event.delivery_id == "delivery-uuid-9988"
    assert event.branch == "develop"
    assert event.repository_name == "nero-enterprise/hotel-billing"
    assert event.head_commit.sha == "c0ffee1234567890abcdef1234567890abcdef12"
    assert event.head_commit.author_name == "Jane Developer"
    assert event.sender == "janedev"


def test_github_adapter_pull_request_event_normalization():
    adapter = GitHubAdapter()
    payload = {
        "action": "opened",
        "number": 42,
        "pull_request": {
            "title": "feat: order split payments",
            "head": {
                "ref": "feature/split-payments",
                "sha": "pr1234567890abcdef",
                "repo": {"full_name": "nero-enterprise/hotel-billing", "clone_url": "https://github.com/nero-enterprise/hotel-billing.git"},
                "user": {"login": "developer-1"}
            },
            "base": {
                "ref": "main",
                "repo": {"full_name": "nero-enterprise/hotel-billing", "clone_url": "https://github.com/nero-enterprise/hotel-billing.git"}
            }
        },
        "sender": {"login": "developer-1"}
    }
    payload_bytes = json.dumps(payload).encode()
    headers = {
        "X-GitHub-Event": "pull_request",
        "X-GitHub-Delivery": "delivery-pr-42"
    }

    event = adapter.parse_webhook_event(headers, payload_bytes)
    assert event is not None
    assert event.event_type == SCMEventType.PULL_REQUEST
    assert event.pr_id == "42"
    assert event.pr_title == "feat: order split payments"
    assert event.source_branch == "feature/split-payments"
    assert event.target_branch == "main"
    assert event.is_fork is False


def test_bitbucket_adapter_verification_and_parsing():
    adapter = BitbucketAdapter()
    secret = "bitbucket-shared-secret"
    payload = {
        "repository": {"full_name": "nero/sample-node-service"},
        "push": {
            "changes": [{
                "new": {
                    "name": "main",
                    "target": {
                        "hash": "bbcommit123",
                        "message": "fix: node memory leak",
                        "author": {"raw": "Bob Engineer"},
                        "date": "2026-11-08T11:00:00Z"
                    }
                }
            }]
        },
        "actor": {"display_name": "Bob"}
    }
    payload_bytes = json.dumps(payload).encode()

    # Test Bearer authorization
    assert adapter.verify_webhook({"Authorization": f"Bearer {secret}"}, payload_bytes, secret) is True
    assert adapter.verify_webhook({"Authorization": "Bearer wrong"}, payload_bytes, secret) is False

    # Test HMAC header
    sig = "sha256=" + hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
    assert adapter.verify_webhook({"X-Hub-Signature": sig}, payload_bytes, secret) is True

    # Test Event Parsing
    headers = {"X-Event-Key": "repo:push", "X-Request-UUID": "bb-uuid-1122"}
    event = adapter.parse_webhook_event(headers, payload_bytes)
    assert event is not None
    assert event.branch == "main"
    assert event.head_commit.sha == "bbcommit123"
    assert event.provider == "bitbucket"


def test_gitlab_adapter_verification_and_parsing():
    adapter = GitLabAdapter()
    secret = "gitlab-token-abc"
    payload = {
        "project": {"path_with_namespace": "nero/sample-go-service", "web_url": "https://gitlab.nero.local/nero/sample-go-service"},
        "ref": "refs/heads/release-1.0",
        "after": "glcommit456",
        "commits": [{
            "id": "glcommit456",
            "message": "release: v1.0.0",
            "author": {"name": "Charlie SRE", "email": "charlie@nero.local"},
            "timestamp": "2026-11-08T12:00:00Z"
        }],
        "user_username": "charlie"
    }
    payload_bytes = json.dumps(payload).encode()

    # Valid token
    assert adapter.verify_webhook({"X-Gitlab-Token": secret}, payload_bytes, secret) is True
    # Invalid token
    assert adapter.verify_webhook({"X-Gitlab-Token": "bad-token"}, payload_bytes, secret) is False

    # Parse push event
    headers = {"X-Gitlab-Event": "Push Hook", "X-Gitlab-Event-UUID": "gl-uuid-7788"}
    event = adapter.parse_webhook_event(headers, payload_bytes)
    assert event is not None
    assert event.branch == "release-1.0"
    assert event.head_commit.sha == "glcommit456"
    assert event.provider == "gitlab"


def test_scm_status_and_comment_publishing():
    gh = GitHubAdapter()
    update = SCMStatusUpdate(
        state=SCMStatusState.SUCCESS,
        context="nero/ci-quality-gate",
        description="All 12 checks passed (Coverage 85%)",
        target_url="http://localhost:8080/job/universal-ci-pipeline/10"
    )
    assert gh.publish_commit_status("https://github.com/repo.git", "sha123", update) is True
    assert len(gh.published_statuses) == 1
    assert gh.published_statuses[0]["state"] == "success"

    comment = SCMComment(pr_id="42", body="### NERO CI Report\nPassed: 100%")
    assert gh.post_pr_comment("https://github.com/repo.git", "42", comment) is True
    assert len(gh.posted_comments) == 1
    assert "NERO CI Report" in gh.posted_comments[0]["body"]
