"""
NERO Platform - Multi-Account AWS STS AssumeRole Mock Fixtures (A1-TST-003)
Simulates AWS Security Token Service (STS) multi-account authentication,
AssumeRole credential generation, management account boundary enforcement,
and session validation without making real AWS network calls or incurring cloud costs ($0.00).
"""

import re
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError


MANAGEMENT_ACCOUNT_ID = "999999999999"
DEVELOP_ACCOUNT_ID = "111122223333"
QA_ACCOUNT_ID = "222233334444"
PROD_ACCOUNT_ID = "333344445555"
CALLER_IDENTITY_ACCOUNT_ID = "111122223333"

ROLE_ARN_PATTERN = re.compile(r"^arn:aws:iam::(\d{12}):role/([a-zA-Z0-9+=,.@\-_/]+)$")
SESSION_NAME_PATTERN = re.compile(r"^[\w+=,.@-]{2,64}$")


class MockSTSClient:
    """
    Mock AWS STS client enforcing enterprise multi-account boundaries:
    1. Rejects any AssumeRole call targeting the Organizations Management Account.
    2. Enforces strict ARN formatting and session name sanitization.
    3. Produces deterministic temporary STS session credentials.
    """

    def __init__(
        self,
        caller_account_id: str = CALLER_IDENTITY_ACCOUNT_ID,
        management_account_id: str = MANAGEMENT_ACCOUNT_ID
    ):
        self.caller_account_id = caller_account_id
        self.management_account_id = management_account_id
        self.assume_role_history = []

    def get_caller_identity(self) -> Dict[str, str]:
        return {
            "UserId": f"AROAEXAMPLE:{self.caller_account_id}",
            "Account": self.caller_account_id,
            "Arn": f"arn:aws:sts::{self.caller_account_id}:assumed-role/CI-CD-Deployer/session"
        }

    def assume_role(
        self,
        RoleArn: str,
        RoleSessionName: str,
        DurationSeconds: int = 3600,
        ExternalId: Optional[str] = None
    ) -> Dict[str, Any]:
        match = ROLE_ARN_PATTERN.match(RoleArn)
        if not match:
            raise ClientError(
                error_response={
                    "Error": {
                        "Code": "ValidationError",
                        "Message": f"The specified Role ARN '{RoleArn}' is not valid."
                    }
                },
                operation_name="AssumeRole"
            )

        target_account_id, role_name = match.groups()

        # Enforce Management Account Boundary (Fail-Closed)
        if target_account_id == self.management_account_id:
            raise ClientError(
                error_response={
                    "Error": {
                        "Code": "AccessDenied",
                        "Message": (
                            f"Security Policy Violation: Deployment into AWS Organizations "
                            f"Management Account '{self.management_account_id}' is strictly forbidden."
                        )
                    }
                },
                operation_name="AssumeRole"
            )

        if not SESSION_NAME_PATTERN.match(RoleSessionName):
            raise ClientError(
                error_response={
                    "Error": {
                        "Code": "ValidationError",
                        "Message": f"RoleSessionName '{RoleSessionName}' must satisfy pattern [\\w+=,.@-]{{2,64}}."
                    }
                },
                operation_name="AssumeRole"
            )

        exp_time = datetime.now(timezone.utc) + timedelta(seconds=DurationSeconds)
        assumed_role_user_arn = f"arn:aws:sts::{target_account_id}:assumed-role/{role_name}/{RoleSessionName}"

        record = {
            "role_arn": RoleArn,
            "session_name": RoleSessionName,
            "target_account_id": target_account_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.assume_role_history.append(record)

        return {
            "Credentials": {
                "AccessKeyId": f"ASIA{target_account_id[:8]}MOCKKEY",
                "SecretAccessKey": f"mockSecretKeyForAccount{target_account_id}",
                "SessionToken": f"mockSessionToken{target_account_id}{RoleSessionName}",
                "Expiration": exp_time
            },
            "AssumedRoleUser": {
                "AssumedRoleId": f"AROA{target_account_id[:8]}:{RoleSessionName}",
                "Arn": assumed_role_user_arn
            },
            "PackedPolicySize": 6
        }
