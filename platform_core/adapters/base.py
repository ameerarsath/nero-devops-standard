"""
NERO Universal Enterprise DevOps Automation Platform
Base Platform Adapter Abstract Interface (A1-FND-001)

Formalizes typed abstract contracts, input/output models, and lifecycle methods
across all build, infrastructure, deployment, and verification adapters.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from platform_core.engine.errors import PlatformException, PlatformErrorCode


class AdapterRequest(BaseModel):
    """Standardized input payload for adapter execution."""
    action: str = Field(description="Action verb, e.g. deploy, build, plan, verify")
    target: str = Field(description="Target identifier, e.g. component name, environment, bucket")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Action-specific parameters")
    context: Dict[str, Any] = Field(default_factory=dict, description="Environment and execution context")


class AdapterResult(BaseModel):
    """Standardized output payload from adapter execution."""
    adapter_name: str = Field(description="Name of the executing adapter")
    success: bool = Field(description="Whether the execution succeeded")
    data: Dict[str, Any] = Field(default_factory=dict, description="Structured execution payload")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    execution_time_seconds: float = Field(default=0.0, description="Duration in seconds")


class BasePlatformAdapter(ABC):
    """Abstract base class for all NERO platform adapters."""

    def __init__(self, adapter_name: str, version: str = "1.0.0"):
        self.adapter_name = adapter_name
        self.version = version

    @abstractmethod
    def validate_prerequisites(self, context: Dict[str, Any]) -> bool:
        """Verifies that all required system binaries, permissions, and dependencies are present."""
        pass

    @abstractmethod
    def execute(self, request: AdapterRequest) -> AdapterResult:
        """Executes the primary adapter operation synchronously and returns an AdapterResult."""
        pass

    def cleanup(self) -> None:
        """Teardown hook for releasing allocated resources, files, or connections."""
        pass

    def handle_error(self, code: PlatformErrorCode, message: str, details: Optional[Dict[str, Any]] = None):
        """Raises a standardized PlatformException attributed to this adapter."""
        raise PlatformException(code=code, message=f"[{self.adapter_name}] {message}", details=details)
