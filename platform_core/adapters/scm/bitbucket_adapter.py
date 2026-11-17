"""
NERO Universal Enterprise DevOps Automation Platform
Bitbucket SCM Webhook Adapter (A3-SCM-003)

Implements Bitbucket Server / Cloud webhook verification, delivery tracking,
and normalization for push and pull request events.
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

logger = logging.getLogger("nero.scm.bitbucket")


class BitbucketAdapter(BaseSCMAdapter):
    """Bitbucket SCM Adapter supporting HMAC signature and token authentication."""

    def __init__(self, api_token: Optional[str] = None):
        super().__init__(provider_name="bitbucket", version="1.0.0")
        self.api_token = api_token
        self.published_statuses: List[Dict[str, Any]] = []
        self.posted_comments: List[Dict[str, Any]] = []

    def verify_webhook(self, headers: Dict[str, str], payload_bytes: bytes, secret: str) -> bool:
        """Verifies Bitbucket webhook via HMAC signature or secret token header."""
        if not secret:
            logger.warning("Bitbucket verification failed: empty secret.")
            return False

        norm_headers = {k.lower(): v for k, v in headers.items()}

        # 1. Check for HMAC header (Bitbucket Server / Cloud HMAC addon)
        sig_header = norm_headers.get("x-hub-signature")
        if sig_header:
            if sig_header.startswith("sha256="):
                expected = sig_header[len("sha256="):].strip()
            else:
                expected = sig_header.strip()
            computed = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected.lower(), computed.lower())

        # 2. Check for Authorization header (Bearer token or token header)
        auth_header = norm_headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[len("Bearer "):].strip()
            return hmac.compare_digest(token, secret)

        # 3. Check for custom secret token header
        token_header = norm_headers.get("x-hook-secret")
        if token_header:
            return hmac.compare_digest(token_header, secret)

        logger.warning("No valid Bitbucket signature or authorization header found.")
        return False

    def parse_webhook_event(
        self, headers: Dict[str, str], payload_bytes: bytes
    ) -> Optional[Union[SCMPushEvent, SCMPullRequestEvent]]:
        """Parses Bitbucket event payload."""
        norm_headers = {k.lower(): v for k, v in headers.items()}
        event_key = norm_headers.get("x-event-key", "")
        delivery_id = norm_headers.get("x-request-uuid", "unknown-delivery")

        try:
            payload = json.loads(payload_bytes.decode("utf-8"))
        except Exception as e:
            logger.error(f"Failed to decode Bitbucket JSON payload: {e}")
            return None

        repo_data = payload.get("repository", {})
        repo_url = (
            repo_data.get("links", {}).get("html", {}).get("href")
            or repo_data.get("full_name")
            or ""
        )
        repo_name = repo_data.get("full_name") or "unknown"

        if event_key == "repo:push":
            changes = payload.get("push", {}).get("changes", [])
            if not changes:
                return None
            change = changes[0]
            new_target = change.get("new") or {}
            branch_name = new_target.get("name", "main")
            target_commit = new_target.get("target") or {}

            author_data = target_commit.get("author", {})
            commit_obj = SCMCommit(
                sha=target_commit.get("hash", "unknown"),
                message=target_commit.get("message", "Bitbucket push commit"),
                author_name=author_data.get("raw", "Unknown"),
                author_email="",
                timestamp=target_commit.get("date", "")
            )

            return SCMPushEvent(
                event_type=SCMEventType.PUSH,
                delivery_id=delivery_id,
                provider="bitbucket",
                repository_url=repo_url,
                repository_name=repo_name,
                branch=branch_name,
                ref=f"refs/heads/{branch_name}",
                head_commit=commit_obj,
                before_sha=(change.get("old") or {}).get("target", {}).get("hash"),
                after_sha=commit_obj.sha,
                sender=(payload.get("actor") or {}).get("display_name", "unknown"),
                raw_payload={"event_key": event_key, "repo": repo_name}
            )

        elif event_key.startswith("pullrequest:"):
            pr_data = payload.get("pullrequest", {})
            action = event_key.replace("pullrequest:", "")
            source = pr_data.get("source", {})
            dest = pr_data.get("destination", {})

            source_repo = source.get("repository", {})
            is_fork = (
                source_repo.get("full_name") is not None
                and dest.get("repository", {}).get("full_name") is not None
                and source_repo.get("full_name") != dest.get("repository", {}).get("full_name")
            )

            commit_obj = SCMCommit(
                sha=(source.get("commit") or {}).get("hash", "unknown"),
                message=pr_data.get("title", ""),
                author_name=(pr_data.get("author") or {}).get("display_name", "Unknown"),
                author_email="",
                timestamp=pr_data.get("updated_on") or pr_data.get("created_on") or ""
            )

            return SCMPullRequestEvent(
                event_type=SCMEventType.PULL_REQUEST,
                delivery_id=delivery_id,
                provider="bitbucket",
                action=action,
                pr_id=str(pr_data.get("id", "0")),
                pr_title=pr_data.get("title", "Bitbucket PR"),
                repository_url=repo_url,
                repository_name=repo_name,
                source_branch=(source.get("branch") or {}).get("name", ""),
                target_branch=(dest.get("branch") or {}).get("name", ""),
                source_repo_url=source_repo.get("links", {}).get("html", {}).get("href", repo_url),
                is_fork=is_fork,
                head_commit=commit_obj,
                sender=(payload.get("actor") or {}).get("display_name", "unknown"),
                raw_payload={"action": action, "id": pr_data.get("id")}
            )

        logger.info(f"Unhandled Bitbucket event: {event_key}")
        return None

    def publish_commit_status(self, repo_url: str, commit_sha: str, status: SCMStatusUpdate) -> bool:
        record = {
            "provider": "bitbucket",
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
            "provider": "bitbucket",
            "repo_url": repo_url,
            "pr_id": pr_id,
            "body": comment.body,
        }
        self.posted_comments.append(record)
        return True
