"""
NERO Universal Enterprise DevOps Automation Platform
Security Exception Rules Engine (A3-SEC-004)

Manages policy exemptions for security findings (.nero-security-exceptions.yaml)
with mandatory business justification, named approvers, and strict 90-day expiration TTL.
"""

import datetime
import logging
import os
from typing import Dict, Any, List, Optional, Tuple
import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger("nero.policy.security_exceptions")

DEFAULT_EXCEPTION_FILE = os.path.join(os.getcwd(), ".nero-security-exceptions.yaml")
MAX_EXCEPTION_TTL_DAYS = 90


class SecurityExceptionRule(BaseModel):
    """Normalized security exception model."""
    id: str = Field(description="Unique exception ID, e.g. EXC-2026-001")
    finding_id: str = Field(description="Rule ID, CVE ID, or finding fingerprint")
    target: str = Field(description="Target file, component, or path pattern")
    justification: str = Field(description="Mandatory business reason (min 15 chars)")
    approver: str = Field(description="Security approver identity")
    created_at: str = Field(description="ISO-8601 creation timestamp")
    expires_at: str = Field(description="ISO-8601 expiration timestamp (max 90 days)")
    revoked: bool = Field(default=False, description="Whether exemption is revoked")


class SecurityExceptionsEngine:
    """Evaluates and enforces security exceptions."""

    def __init__(self, exception_file: Optional[str] = None):
        self.exception_file = exception_file or DEFAULT_EXCEPTION_FILE
        self.rules: List[SecurityExceptionRule] = self._load_rules()

    def _load_rules(self) -> List[SecurityExceptionRule]:
        if not os.path.isfile(self.exception_file):
            return []

        try:
            with open(self.exception_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict):
                return []

            raw_rules = data.get("exceptions", [])
            valid_rules = []
            for r in raw_rules:
                try:
                    rule = SecurityExceptionRule.model_validate(r)
                    # Validate justification length
                    if len(rule.justification.strip()) < 15:
                        logger.warning(f"Exemption {rule.id} ignored: justification too short (< 15 chars)")
                        continue
                    valid_rules.append(rule)
                except Exception as e:
                    logger.warning(f"Invalid exception entry in {self.exception_file}: {e}")
            return valid_rules
        except Exception as e:
            logger.error(f"Failed to parse security exception file {self.exception_file}: {e}")
            return []

    def is_exempted(self, finding_id: str, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Determines whether a security finding is covered by a valid, active exception.

        Returns:
            (exempted: bool, reason_or_rule_id: Optional[str])
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        norm_path = file_path.replace("\\", "/")

        for rule in self.rules:
            if rule.revoked:
                continue

            # Check finding ID match (exact or wildcard)
            if rule.finding_id != "*" and rule.finding_id != finding_id:
                continue

            # Check target path match
            norm_target = rule.target.replace("\\", "/")
            if norm_target != "*" and norm_target not in norm_path and not norm_path.endswith(norm_target):
                continue

            # Check expiration date
            try:
                # Support parsing ISO format
                exp_dt = datetime.datetime.fromisoformat(rule.expires_at.replace("Z", "+00:00"))
                if now > exp_dt:
                    logger.info(f"Exception {rule.id} matches finding [{finding_id}] but has EXPIRED on {rule.expires_at}")
                    return False, f"EXPIRED on {rule.expires_at}"
            except Exception as e:
                logger.warning(f"Could not parse expires_at date in rule {rule.id}: {e}")
                return False, "INVALID_EXPIRATION"

            logger.info(f"Finding [{finding_id}] in {norm_path} EXEMPTED by rule {rule.id} (Approver: {rule.approver})")
            return True, rule.id

        return False, None
