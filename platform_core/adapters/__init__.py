"""
NERO Universal Enterprise DevOps Automation Platform - Base Adapter Contract
Defines the standard abstract contract and lifecycle for all platform adapters.
"""

from typing import Dict, Any, Optional

from platform_core.adapters.base import (
    BasePlatformAdapter,
    AdapterRequest,
    AdapterResult
)
from platform_core.engine.errors import PlatformException, PlatformErrorCode


class BaseAdapter(BasePlatformAdapter):
    """
    Standard BaseAdapter inheriting from BasePlatformAdapter for backward compatibility
    and uniform polymorphism.
    """

    def __init__(self, adapter_name: str, version: str = "1.0.0"):
        super().__init__(adapter_name=adapter_name, version=version)

    def validate_prerequisites(self, context: Dict[str, Any]) -> bool:
        """Default prerequisite validation (overridden by subclasses)."""
        return True

    def execute(self, request: AdapterRequest) -> AdapterResult:
        """
        Default dispatcher for execute() request wrapper. Subclasses can override
        or implement domain-specific methods (e.g. deploy, build).
        """
        return AdapterResult(
            adapter_name=self.adapter_name,
            success=True,
            data={"status": "executed", "request": request.model_dump()}
        )


__all__ = [
    "BasePlatformAdapter",
    "BaseAdapter",
    "AdapterRequest",
    "AdapterResult"
]
