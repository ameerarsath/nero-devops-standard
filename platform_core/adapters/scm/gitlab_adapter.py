"""
NERO Universal Enterprise DevOps Automation Platform
GitLab SCM Webhook Adapter (A3-SCM-003)

Implements GitLab secret token verification with constant-time comparison,
delivery ID tracking, and payload normalization for Push and Merge Request events.
"""

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

logger = logging.getLogger("nero.scm.gitlab")


class GitLabAdapter(BaseSCMAdapter):
    """GitLab SCM Adapter supporting secret token header authentication."""

    def __init__(self, api_token: Optional[str] = None):
        super().__init__(provider_name="gitlab", version="1.0.0")
        self.api_token = api_token
        self.published_statuses: List[Dict[str, Any]] = []
        self.posted_comments: List[Dict[str, Any]] = []

    def verify_webhook(self, headers: Dict[str, str], payload_bytes: bytes, secret: str) -> bool:
        """Verifies GitLab X-Gitlab-Token header using constant-time comparison."""
        if not secret:
            logger.warning("GitLab verification failed: empty secret.")
            return False

        norm_headers = {k.lower(): v for k, v in headers.items()}
        token_header = norm_headers.get("x-gitlab-token")

        if not token_header:
            logger.warning("Missing X-Gitlab-Token header.")
            return False

        # Constant-time comparison
        return hmac.compare_digest(token_header, secret)

    def parse_webhook_event(
        self, headers: Dict[str, str], payload_bytes: bytes
    ) -> Optional[Union[SCMPushEvent, SCMPullRequestEvent]]:
        """Parses GitLab webhook payload into normalized event models."""
        norm_headers = {k.lower(): v for k, v in headers.items()}
        event_name = norm_headers.get("x-gitlab-event", "")
        delivery_id = norm_headers.get("x-gitlab-event-uuid", "unknown-delivery")

        try:
            payload = json.loads(payload_bytes.decode("utf-8"))
        except Exception as e:
            logger.error(f"Failed to decode GitLab JSON payload: {e}")
            return None

        project_data = payload.get("project", {})
        repo_url = project_data.get("web_url") or project_data.get("git_http_url") or ""
        repo_name = project_data.get("path_with_namespace") or "unknown"

        if event_name in ("Push Hook", "push"):
            ref = payload.get("ref", "")
            branch = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else ref
            commits = payload.get("commits", [])
            last_commit = commits[-1] if commits else {}

            author_data = last_commit.get("author", {})
            commit_obj = SCMCommit(
                sha=last_commit.get("id") or payload.get("after") or "unknown",
                message=last_commit.get("message", "GitLab push commit"),
                author_name=author_data.get("name") or payload.get("user_name") or "Unknown",
                author_email=author_data.get("email", ""),
                timestamp=last_commit.get("timestamp", "")
            )

            return SCMPushEvent(
                event_type=SCMEventType.PUSH,
                delivery_id=delivery_id,
                provider="gitlab",
                repository_url=repo_url,
                repository_name=repo_name,
                branch=branch,
                ref=ref,
                head_commit=commit_obj,
                before_sha=payload.get("before"),
                after_sha=payload.get("after") or commit_obj.sha,
                sender=payload.get("user_username") or "unknown",
                raw_payload={"ref": ref, "project": repo_name}
            )

        elif event_name in ("Merge Request Hook", "merge_request"):
            attrs = payload.get("object_attributes", {})
            action = attrs.get("action", "unknown")
            last_commit = attrs.get("last_commit", {})
            author_data = last_commit.get("author", {})

            is_fork = attrs.get("source_project_id") != attrs.get("target_project_id")

            commit_obj = SCMCommit(
                sha=last_commit.get("id") or attrs.get("last_commit_id") or "unknown",
                message=attrs.get("title", ""),
                author_name=author_data.get("name") or (payload.get("user") or {}).get("name") or "Unknown",
                author_email=author_data.get("email", ""),
                timestamp=attrs.get("updated_at") or attrs.get("created_at") or ""
            )

            return SCMPullRequestEvent(
                event_type=SCMEventType.PULL_REQUEST,
                delivery_id=delivery_id,
                provider="gitlab",
                action=action,
                pr_id=str(attrs.get("iid") or attrs.get("id") or "0"),
                pr_title=attrs.get("title", "GitLab MR"),
                repository_url=repo_url,
                repository_name=repo_name,
                source_branch=attrs.get("source_branch", ""),
                target_branch=attrs.get("target_branch", ""),
                source_repo_url=attrs.get("source", {}).get("web_url", repo_url),
                is_fork=is_fork,
                head_commit=commit_obj,
                sender=(payload.get("user") or {}).get("username", "unknown"),
                raw_payload={"action": action, "iid": attrs.get("iid")}
            )

        logger.info(f"Unhandled GitLab event: {event_name}")
        return None

    def publish_commit_status(self, repo_url: str, commit_sha: str, status: SCMStatusUpdate) -> bool:
        record = {
            "provider": "gitlab",
            "repo_url": repo_url,
            "commit_sha": commit_sha,
            "state": status.state.value,
            "context": status.context,
            "description": status.description,
            "target_url": status.target_url,
        }
        self.published_statuses.append(record)
        return True

    def post_pr_comment(self, repo_url: str, pr_id: str, comment: SCMComment) -> bool:
        record = {
            "provider": "gitlab",
            "repo_url": repo_url,
            "pr_id": pr_id,
            "body": comment.body,
        }
        self.posted_comments.append(record)
        return True
