"""
NERO Universal Enterprise DevOps Automation Platform
SCM Provider Adapter Base Contract (A3-SCM-001)

Codifies typed abstract contracts, normalized SCM event models, and webhook
verification interfaces across Git SCM providers (GitHub, Bitbucket, GitLab).
"""

from abc import abstractmethod
from enum import Enum
from typing import Dict, Any, Optional, Union
from pydantic import BaseModel, Field

from platform_core.adapters.base import BasePlatformAdapter, AdapterRequest, AdapterResult


class SCMEventType(str, Enum):
    """Normalized SCM Event Types."""
    PUSH = "push"
    PULL_REQUEST = "pull_request"
    PING = "ping"
    TAG = "tag"


class SCMCommit(BaseModel):
    """Normalized commit metadata."""
    sha: str = Field(description="Full or abbreviated commit SHA")
    message: str = Field(description="Commit message")
    author_name: str = Field(default="Unknown", description="Author name")
    author_email: str = Field(default="", description="Author email")
    timestamp: str = Field(default="", description="ISO-8601 commit timestamp")


class SCMPushEvent(BaseModel):
    """Normalized Push Event Model."""
    event_type: SCMEventType = SCMEventType.PUSH
    delivery_id: str = Field(description="Unique delivery UUID from SCM provider")
    provider: str = Field(description="SCM provider name (github, bitbucket, gitlab)")
    repository_url: str = Field(description="Canonical clone/repo URL")
    repository_name: str = Field(description="Repository full name, e.g. org/repo")
    branch: str = Field(description="Target branch name, e.g. main, develop")
    ref: str = Field(description="Full Git ref, e.g. refs/heads/main")
    head_commit: SCMCommit = Field(description="Head commit object")
    before_sha: Optional[str] = Field(default=None, description="SHA before push")
    after_sha: str = Field(description="SHA after push")
    sender: str = Field(default="unknown", description="Username triggering the push")
    raw_payload: Dict[str, Any] = Field(default_factory=dict, description="Redacted raw payload")


class SCMPullRequestEvent(BaseModel):
    """Normalized Pull Request Event Model."""
    event_type: SCMEventType = SCMEventType.PULL_REQUEST
    delivery_id: str = Field(description="Unique delivery UUID from SCM provider")
    provider: str = Field(description="SCM provider name (github, bitbucket, gitlab)")
    action: str = Field(description="PR action: opened, synchronize, reopened, closed")
    pr_id: str = Field(description="Pull request number or ID as string")
    pr_title: str = Field(description="Title of the pull request")
    repository_url: str = Field(description="Canonical base repository URL")
    repository_name: str = Field(description="Repository full name")
    source_branch: str = Field(description="Source feature branch name")
    target_branch: str = Field(description="Target base branch name (e.g. main, develop)")
    source_repo_url: str = Field(description="Source repository URL (differs if fork)")
    is_fork: bool = Field(default=False, description="Whether PR originated from a fork")
    head_commit: SCMCommit = Field(description="Head commit of the pull request branch")
    sender: str = Field(default="unknown", description="Username who opened/updated PR")
    raw_payload: Dict[str, Any] = Field(default_factory=dict, description="Redacted raw payload")


class SCMStatusState(str, Enum):
    """SCM Commit Status States."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"


class SCMStatusUpdate(BaseModel):
    """Payload for publishing commit or PR status back to SCM."""
    state: SCMStatusState = Field(description="Target status state")
    context: str = Field(default="nero/ci-pipeline", description="Status check identifier")
    description: str = Field(description="Human-readable status summary")
    target_url: Optional[str] = Field(default=None, description="Link to build logs or report")


class SCMComment(BaseModel):
    """Payload for posting summary comments to pull requests."""
    pr_id: str = Field(description="Pull request number or ID")
    body: str = Field(description="Markdown-formatted comment body")


class BaseSCMAdapter(BasePlatformAdapter):
    """Abstract contract for all Git SCM provider adapters."""

    def __init__(self, provider_name: str, version: str = "1.0.0"):
        super().__init__(adapter_name=f"scm-{provider_name}", version=version)
        self.provider_name = provider_name

    def validate_prerequisites(self, context: Dict[str, Any]) -> bool:
        """SCM adapters do not require local CLI binaries by default."""
        return True

    def execute(self, request: AdapterRequest) -> AdapterResult:
        """Standard AdapterRequest execution dispatch."""
        action = request.action
        if action == "verify":
            headers = request.parameters.get("headers", {})
            payload = request.parameters.get("payload_bytes", b"")
            secret = request.parameters.get("secret", "")
            valid = self.verify_webhook(headers=headers, payload_bytes=payload, secret=secret)
            return AdapterResult(
                adapter_name=self.adapter_name,
                success=valid,
                data={"verified": valid},
                error_message=None if valid else "Webhook signature verification failed"
            )
        elif action == "parse":
            headers = request.parameters.get("headers", {})
            payload = request.parameters.get("payload_bytes", b"")
            event = self.parse_webhook_event(headers=headers, payload_bytes=payload)
            if event:
                return AdapterResult(
                    adapter_name=self.adapter_name,
                    success=True,
                    data={"event": event.model_dump()}
                )
            return AdapterResult(
                adapter_name=self.adapter_name,
                success=False,
                error_message="Failed to parse webhook event"
            )
        elif action == "publish_status":
            repo_url = request.parameters.get("repo_url", "")
            commit_sha = request.parameters.get("commit_sha", "")
            status = SCMStatusUpdate(**request.parameters.get("status", {}))
            ok = self.publish_commit_status(repo_url, commit_sha, status)
            return AdapterResult(adapter_name=self.adapter_name, success=ok, data={"published": ok})
        elif action == "post_comment":
            repo_url = request.parameters.get("repo_url", "")
            comment = SCMComment(**request.parameters.get("comment", {}))
            ok = self.post_pr_comment(repo_url, comment.pr_id, comment)
            return AdapterResult(adapter_name=self.adapter_name, success=ok, data={"posted": ok})
        else:
            return AdapterResult(
                adapter_name=self.adapter_name,
                success=False,
                error_message=f"Unsupported SCM action: {action}"
            )

    @abstractmethod
    def verify_webhook(self, headers: Dict[str, str], payload_bytes: bytes, secret: str) -> bool:
        """Verifies cryptographic signature or authentication header for this provider."""
        pass

    @abstractmethod
    def parse_webhook_event(
        self, headers: Dict[str, str], payload_bytes: bytes
    ) -> Optional[Union[SCMPushEvent, SCMPullRequestEvent]]:
        """Parses and normalizes the provider raw payload into standard event models."""
        pass

    @abstractmethod
    def publish_commit_status(self, repo_url: str, commit_sha: str, status: SCMStatusUpdate) -> bool:
        """Publishes commit check status back to SCM provider API."""
        pass

    @abstractmethod
    def post_pr_comment(self, repo_url: str, pr_id: str, comment: SCMComment) -> bool:
        """Posts structured markdown feedback back to pull request."""
        pass
