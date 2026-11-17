"""
Enterprise Universal Application Delivery Platform - Build Adapter Contract
"""

from abc import abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from platform_core.adapters import BaseAdapter
from platform_core.engine.models import ComponentModel


class BuildResult(BaseModel):
    component_name: str
    artifact_type: str  # container_image or static_tarball
    image_tag: Optional[str] = None
    image_digest: Optional[str] = None
    artifact_path: Optional[str] = None
    checksum_sha256: Optional[str] = None
    sbom_path: Optional[str] = None
    build_metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseBuildAdapter(BaseAdapter):
    """Abstract interface for all language and container build adapters."""

    @abstractmethod
    def build(self, component: ComponentModel, workspace_root: str, release_id: str) -> BuildResult:
        """Executes the build process and returns an immutable BuildResult."""
        pass
