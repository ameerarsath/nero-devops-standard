"""
NERO Universal Enterprise DevOps Automation Platform
GitHub SCM Webhook Adapter (A3-SCM-002)

Implements HMAC-SHA256 signature verification with constant-time comparison,
delivery ID tracking, and payload normalization for GitHub push and pull_request events.
"""

import hashlib
import hmac
import json
import logging
from typing import Dict, Any, Optional, Union, List

from platform_core.adapters.scm.base import (
    BaseSCMAdapter,
    SCMEventType,
    SCMPushEvent,
    SCMPullRequestEvent,
    SCMCommit,
    SCMStatusUpdate,
    SCMComment,
)

logger = logging.getLogger("nero.scm.github")


class GitHubAdapter(BaseSCMAdapter):
    """GitHub SCM Adapter with HMAC-SHA256 signature verification."""

    def __init__(self, api_token: Optional[str] = None):
        super().__init__(provider_name="github", version="1.0.0")
        self.api_token = api_token
        # In-memory record of published statuses and comments for local offline verification
        self.published_statuses: List[Dict[str, Any]] = []
        self.posted_comments: List[Dict[str, Any]] = []

    def verify_webhook(self, headers: Dict[str, str], payload_bytes: bytes, secret: str) -> bool:
        """Verifies X-Hub-Signature-256 header using constant-time HMAC-SHA256."""
        if not secret:
            logger.warning("Webhook verification rejected: empty secret provided.")
            return False

        # Case-insensitive header lookup
        normalized_headers = {k.lower(): v for k, v in headers.items()}
        signature_header = normalized_headers.get("x-hub-signature-256")

        if not signature_header:
            logger.warning("Missing X-Hub-Signature-256 header.")
            return False

        if not signature_header.startswith("sha256="):
            logger.warning("Invalid X-Hub-Signature-256 format; must start with sha256=")
            return False

        expected_sig = signature_header[len("sha256="):].strip()
        computed_sig = hmac.new(
            secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()

        # Strictly use constant-time comparison to prevent timing attacks
        is_valid = hmac.compare_digest(expected_sig.lower(), computed_sig.lower())
        if not is_valid:
            logger.warning("X-Hub-Signature-256 mismatch: signature verification failed.")
        return is_valid

    def parse_webhook_event(
        self, headers: Dict[str, str], payload_bytes: bytes
    ) -> Optional[Union[SCMPushEvent, SCMPullRequestEvent]]:
        """Parses raw GitHub webhook payload into normalized event models."""
        normalized_headers = {k.lower(): v for k, v in headers.items()}
        event_type = normalized_headers.get("x-github-event", "")
        delivery_id = normalized_headers.get("x-github-delivery", "unknown-delivery")

        try:
            payload = json.loads(payload_bytes.decode("utf-8"))
        except Exception as e:
            logger.error(f"Failed to decode JSON payload: {e}")
            return None

        if event_type == "push":
            ref = payload.get("ref", "")
            branch = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else ref
            head_commit_data = payload.get("head_commit") or {}
            commits = payload.get("commits") or []
            if not head_commit_data and commits:
                head_commit_data = commits[-1]

            author_data = head_commit_data.get("author", {})
            commit_obj = SCMCommit(
                sha=head_commit_data.get("id") or payload.get("after") or "unknown",
                message=head_commit_data.get("message", "No commit message"),
                author_name=author_data.get("name", "Unknown"),
                author_email=author_data.get("email", ""),
                timestamp=head_commit_data.get("timestamp", "")
            )

            repo_data = payload.get("repository", {})
            return SCMPushEvent(
                event_type=SCMEventType.PUSH,
                delivery_id=delivery_id,
                provider="github",
                repository_url=repo_data.get("clone_url") or repo_data.get("html_url") or "",
                repository_name=repo_data.get("full_name") or repo_data.get("name") or "unknown",
                branch=branch,
                ref=ref,
                head_commit=commit_obj,
                before_sha=payload.get("before"),
                after_sha=payload.get("after") or commit_obj.sha,
                sender=(payload.get("sender") or {}).get("login", "unknown"),
                raw_payload={"ref": ref, "repository": repo_data.get("full_name")}
            )

        elif event_type == "pull_request":
            pr_data = payload.get("pull_request", {})
            action = payload.get("action", "unknown")
            head = pr_data.get("head", {})
            base = pr_data.get("base", {})
            base_repo = base.get("repo", {})
            head_repo = head.get("repo", {}) or {}

            is_fork = (
                base_repo.get("full_name") is not None
                and head_repo.get("full_name") is not None
                and base_repo.get("full_name") != head_repo.get("full_name")
            )

            head_user = head.get("user", {})
            commit_obj = SCMCommit(
                sha=head.get("sha", "unknown"),
                message=pr_data.get("title", ""),
                author_name=head_user.get("login", "Unknown"),
                author_email="",
                timestamp=pr_data.get("updated_at") or pr_data.get("created_at") or ""
            )

            return SCMPullRequestEvent(
                event_type=SCMEventType.PULL_REQUEST,
                delivery_id=delivery_id,
                provider="github",
                action=action,
                pr_id=str(payload.get("number") or pr_data.get("number") or "0"),
                pr_title=pr_data.get("title", "Untitled PR"),
                repository_url=base_repo.get("clone_url") or base_repo.get("html_url") or "",
                repository_name=base_repo.get("full_name") or base_repo.get("name") or "unknown",
                source_branch=head.get("ref", ""),
                target_branch=base.get("ref", ""),
                source_repo_url=head_repo.get("clone_url") or head_repo.get("html_url") or "",
                is_fork=is_fork,
                head_commit=commit_obj,
                sender=(payload.get("sender") or {}).get("login", "unknown"),
                raw_payload={"action": action, "number": pr_data.get("number")}
            )

        elif event_type == "ping":
            logger.info("Received GitHub ping webhook event.")
            return None

        else:
            logger.info(f"Unhandled GitHub event type: {event_type}")
            return None

    def publish_commit_status(self, repo_url: str, commit_sha: str, status: SCMStatusUpdate) -> bool:
        """Records status for local verification and mock testing."""
        record = {
            "provider": "github",
            "repo_url": repo_url,
            "commit_sha": commit_sha,
            "state": status.state.value,
            "context": status.context,
            "description": status.description,
            "target_url": status.target_url,
        }
        self.published_statuses.append(record)
        logger.info(f"[GitHub Mock SCM] Status recorded for {commit_sha[:8]}: {status.state.value} ({status.description})")
        return True

    def post_pr_comment(self, repo_url: str, pr_id: str, comment: SCMComment) -> bool:
        """Records PR comment for local verification."""
        record = {
            "provider": "github",
            "repo_url": repo_url,
            "pr_id": pr_id,
            "body": comment.body,
        }
        self.posted_comments.append(record)
        logger.info(f"[GitHub Mock SCM] Comment posted to PR #{pr_id}")
        return True
