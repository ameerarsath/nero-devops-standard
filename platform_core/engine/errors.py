"""
NERO Universal Enterprise DevOps Automation Platform - Typed Error Hierarchy
Provides structured error classifications across all platform components and adapters
with standardized deterministic exit codes (A1-FND-002).
"""

from enum import Enum
from typing import Optional, Dict, Any


class PlatformErrorCode(str, Enum):
    CONFIGURATION_ERROR        = "CONFIGURATION_ERROR"
    AUTHENTICATION_ERROR       = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR        = "AUTHORIZATION_ERROR"
    VALIDATION_ERROR           = "VALIDATION_ERROR"
    BUILD_FAILURE              = "BUILD_FAILURE"
    ARTIFACT_INTEGRITY_FAILURE = "ARTIFACT_INTEGRITY_FAILURE"
    INFRASTRUCTURE_FAILURE     = "INFRASTRUCTURE_FAILURE"
    RESOURCE_CONFLICT          = "RESOURCE_CONFLICT"
    RATE_LIMITED               = "RATE_LIMITED"
    DEPLOYMENT_FAILURE         = "DEPLOYMENT_FAILURE"
    HEALTH_CHECK_FAILURE       = "HEALTH_CHECK_FAILURE"
    TIMEOUT                    = "TIMEOUT"
    ROLLBACK_FAILURE           = "ROLLBACK_FAILURE"
    STATE_LOCK_FAILURE         = "STATE_LOCK_FAILURE"
    GOVERNANCE_VIOLATION       = "GOVERNANCE_VIOLATION"


# Deterministic Exit Codes (NERO Standard)
EXIT_CODE_SUCCESS = 0
EXIT_CODE_GENERAL_ERROR = 1
EXIT_CODE_SPEC_ERROR = 10
EXIT_CODE_CATALOG_ERROR = 15
EXIT_CODE_POLICY_ERROR = 20
EXIT_CODE_INFRA_ERROR = 30
EXIT_CODE_DEPLOY_ERROR = 40
EXIT_CODE_VERIFY_ERROR = 50
EXIT_CODE_GOVERNANCE_ERROR = 60


class PlatformException(Exception):
    """Base exception for all platform operations with structured telemetry support."""

    default_exit_code: int = EXIT_CODE_GENERAL_ERROR

    def __init__(
        self,
        code: PlatformErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = False,
        exit_code: Optional[int] = None
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}
        self.recoverable = recoverable
        self.exit_code = exit_code if exit_code is not None else self.default_exit_code

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.code.value,
            "message": self.message,
            "details": self.details,
            "recoverable": self.recoverable,
            "exit_code": self.exit_code
        }

    def __str__(self) -> str:
        return f"[{self.code.value}] {self.message}"


class ConfigurationError(PlatformException):
    default_exit_code: int = EXIT_CODE_GENERAL_ERROR

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, exit_code: Optional[int] = None):
        super().__init__(PlatformErrorCode.CONFIGURATION_ERROR, message, details, recoverable=False, exit_code=exit_code)


class SpecValidationError(PlatformException):
    default_exit_code: int = EXIT_CODE_SPEC_ERROR

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, exit_code: Optional[int] = None):
        super().__init__(PlatformErrorCode.VALIDATION_ERROR, message, details, recoverable=False, exit_code=exit_code)


class SecurityPolicyError(PlatformException):
    default_exit_code: int = EXIT_CODE_POLICY_ERROR

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, exit_code: Optional[int] = None):
        super().__init__(PlatformErrorCode.AUTHORIZATION_ERROR, message, details, recoverable=False, exit_code=exit_code)


class CatalogAuthorizationError(SecurityPolicyError):
    default_exit_code: int = EXIT_CODE_CATALOG_ERROR

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, exit_code: Optional[int] = None):
        super().__init__(message, details, exit_code=exit_code or EXIT_CODE_CATALOG_ERROR)
        self.code = PlatformErrorCode.AUTHORIZATION_ERROR


class InfrastructureError(PlatformException):
    default_exit_code: int = EXIT_CODE_INFRA_ERROR

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, recoverable: bool = False, exit_code: Optional[int] = None):
        super().__init__(PlatformErrorCode.INFRASTRUCTURE_FAILURE, message, details, recoverable=recoverable, exit_code=exit_code)


class DeploymentError(PlatformException):
    default_exit_code: int = EXIT_CODE_DEPLOY_ERROR

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, recoverable: bool = False, exit_code: Optional[int] = None):
        super().__init__(PlatformErrorCode.DEPLOYMENT_FAILURE, message, details, recoverable=recoverable, exit_code=exit_code)


class DeploymentVerificationError(PlatformException):
    default_exit_code: int = EXIT_CODE_VERIFY_ERROR

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, exit_code: Optional[int] = None):
        super().__init__(PlatformErrorCode.HEALTH_CHECK_FAILURE, message, details, recoverable=True, exit_code=exit_code)


class GovernancePolicyError(ConfigurationError):
    default_exit_code: int = EXIT_CODE_GOVERNANCE_ERROR

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, exit_code: Optional[int] = None):
        super().__init__(message, details, exit_code=exit_code or EXIT_CODE_GOVERNANCE_ERROR)
        self.code = PlatformErrorCode.GOVERNANCE_VIOLATION


# Clean Typed Aliases for Platform Components
PlatformError = PlatformException
SpecError = SpecValidationError
CatalogError = CatalogAuthorizationError
PolicyError = SecurityPolicyError
InfraError = InfrastructureError
DeployError = DeploymentError
VerifyError = DeploymentVerificationError
GovernanceError = GovernancePolicyError
