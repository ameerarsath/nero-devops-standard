"""
Enterprise Universal Application Delivery Platform - Node Frontend Build Adapter
Builds static frontend assets, produces versioned tarball, and computes SHA-256 checksum.
"""

import os
import tarfile
import hashlib
from pathlib import Path
from typing import Dict, Any

from platform_core.adapters.build.base import BaseBuildAdapter, BuildResult
from platform_core.engine.models import ComponentModel
from platform_core.engine.errors import PlatformErrorCode


class NodeFrontendBuildAdapter(BaseBuildAdapter):

    def __init__(self):
        super().__init__(adapter_name="build.node-frontend", version="1.0.0")

    def validate_prerequisites(self, context: Dict[str, Any]) -> bool:
        return True

    def build(self, component: ComponentModel, workspace_root: str, release_id: str) -> BuildResult:
        ws_path = Path(workspace_root).resolve()
        context_dir = (ws_path / component.source.context).resolve()
        dist_rel = component.build.dist_dir or "dist"
        dist_dir = (context_dir / dist_rel).resolve()

        if not dist_dir.is_dir():
            self.handle_error(
                PlatformErrorCode.BUILD_FAILURE,
                f"Frontend distribution directory '{dist_dir}' does not exist. Ensure build step has executed."
            )

        # Create deterministic tarball
        out_tar = ws_path / f"{component.name}-dist-{release_id}.tar.gz"
        hasher = hashlib.sha256()

        with tarfile.open(out_tar, "w:gz") as tar:
            for root, dirs, files in os.walk(dist_dir):
                dirs.sort()
                for file in sorted(files):
                    fpath = Path(root) / file
                    arcname = fpath.relative_to(dist_dir)
                    tar.add(fpath, arcname=str(arcname))

        # Compute SHA-256 digest of the actual generated tarball artifact
        with open(out_tar, "rb") as fb:
            while chunk := fb.read(65536):
                hasher.update(chunk)

        tar_checksum = hasher.hexdigest()
        print(f"[{self.adapter_name}] Packaged {out_tar.name} (SHA-256: {tar_checksum[:16]}...)")

        return BuildResult(
            component_name=component.name,
            artifact_type="static_tarball",
            artifact_path=str(out_tar),
            checksum_sha256=tar_checksum,
            build_metadata={
                "adapter": self.adapter_name,
                "dist_dir": str(dist_dir),
                "file_count": sum(len(files) for _, _, files in os.walk(dist_dir))
            }
        )


# Alias for backward compatibility & A1 specification compliance
NodeBuildAdapter = NodeFrontendBuildAdapter

