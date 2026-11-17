"""
NERO Universal Enterprise DevOps Automation Platform
SCM Status and Developer Feedback Publisher (A3-TRG-004)

Formats and publishes commit check statuses and structured markdown summary tables
back to SCM pull requests with strict credential scrubbing and diagnostic sanitization.
"""

import io
import logging
from typing import Optional

from platform_core.adapters.scm.base import (
    BaseSCMAdapter,
    SCMStatusUpdate,
    SCMStatusState,
    SCMComment,
)
from platform_core.ci.pr_validator import PRValidationReport
from platform_core.engine.cli import SecretScrubber

logger = logging.getLogger("nero.ci.feedback_publisher")


def scrub_text(text: str) -> str:
    """Uses platform SecretScrubber to redact credentials, passwords, and tokens."""
    buf = io.StringIO()
    scrubber = SecretScrubber(buf)
    scrubber.write(text)
    return buf.getvalue()


class FeedbackPublisher:
    """Formats and posts CI status checks and PR summary tables back to SCM."""

    def __init__(self, scm_adapter: BaseSCMAdapter):
        self.scm_adapter = scm_adapter

    def publish_validation_report(
        self,
        report: PRValidationReport,
        repo_url: str,
        commit_sha: str,
        build_url: Optional[str] = None
    ) -> bool:
        """Publishes both commit status and markdown PR comment."""
        # 1. Commit Status
        status_state = SCMStatusState.SUCCESS if report.overall_passed else SCMStatusState.FAILURE
        status_description = (
            f"NERO CI: {report.passed_steps}/{report.total_steps} checks passed"
            if report.overall_passed
            else f"NERO CI: FAILED ({report.failed_steps} checks failed)"
        )

        status_update = SCMStatusUpdate(
            state=status_state,
            context="nero/ci-validation",
            description=status_description,
            target_url=build_url
        )

        status_ok = self.scm_adapter.publish_commit_status(
            repo_url=repo_url,
            commit_sha=commit_sha,
            status=status_update
        )

        # 2. Markdown PR Comment Table
        markdown_body = self._render_markdown_table(report, commit_sha, build_url)
        # Scrub any potential secrets or sensitive internal strings
        sanitized_body = scrub_text(markdown_body)

        comment = SCMComment(pr_id=report.pr_id, body=sanitized_body)
        comment_ok = self.scm_adapter.post_pr_comment(
            repo_url=repo_url,
            pr_id=report.pr_id,
            comment=comment
        )

        return status_ok and comment_ok

    def _render_markdown_table(
        self,
        report: PRValidationReport,
        commit_sha: str,
        build_url: Optional[str]
    ) -> str:
        """Builds clean GitHub-flavored markdown summary table."""
        status_badge = "PASSED" if report.overall_passed else "FAILED"
        lines = [
            "### NERO Continuous Integration Summary",
            f"**Application:** `{report.application_id}` | **Commit:** `{commit_sha[:8]}` | **Status:** **{status_badge}**",
            f"Passed Checks: **{report.passed_steps}/{report.total_steps}**",
            "",
            "| # | Validation Step | Status | Verification Detail |",
            "| :---: | :--- | :---: | :--- |"
        ]

        for s in report.steps:
            icon = "PASS" if s.passed else "FAIL"
            lines.append(f"| {s.step_number} | {s.step_name} | **{icon}** | {s.details} |")

        if report.diagnostics:
            lines.append("")
            lines.append("#### Actionable Diagnostics")
            for diag in report.diagnostics:
                lines.append(f"- {diag}")

        if build_url:
            lines.append("")
            lines.append(f"[View Full CI Build Console]({build_url})")

        return "\n".join(lines)
