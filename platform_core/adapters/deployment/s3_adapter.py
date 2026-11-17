"""
Enterprise Universal Application Delivery Platform - S3 Frontend Deployment Adapter
Uploads static frontend assets with strict MIME types, caching policies, and Floci dual-sync.
"""

import os
import mimetypes
import urllib.request
from pathlib import Path
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from platform_core.adapters import BaseAdapter
from platform_core.engine.resolver import ResolvedEnvironmentContext
from platform_core.engine.errors import PlatformErrorCode


class S3DeployResult(BaseModel):
    bucket_name: str
    target_platform: str
    uploaded_files: List[str] = Field(default_factory=list)
    website_url: str


MIME_MAP = {
    ".html": "text/html",
    ".js":   "text/javascript",
    ".css":  "text/css",
    ".svg":  "image/svg+xml",
    ".json": "application/json",
    ".png":  "image/png",
    ".ico":  "image/x-icon",
    ".woff": "font/woff",
    ".woff2":"font/woff2"
}


class S3FrontendDeploymentAdapter(BaseAdapter):

    def __init__(self):
        super().__init__(adapter_name="deploy.s3-static", version="1.0.0")

    def validate_prerequisites(self, context: Dict[str, Any]) -> bool:
        return True

    def deploy(
        self,
        context: ResolvedEnvironmentContext,
        bucket_name: str,
        dist_dir: str
    ) -> S3DeployResult:
        self.validate_prerequisites({})
        dist_path = Path(dist_dir).resolve()
        if not dist_path.is_dir():
            self.handle_error(
                PlatformErrorCode.DEPLOYMENT_FAILURE,
                f"Frontend distribution directory not found: {dist_dir}"
            )

        uploaded = []
        endpoint = context.floci_endpoint or "http://localhost:4566"

        print(f"[{self.adapter_name}] Syncing frontend to bucket '{bucket_name}' ({context.target_platform})...")

        # In Floci, upload to target account and default 000000000000 namespace for browser access
        accounts_to_sync = [context.account_id]
        if context.target_platform == "floci" and context.account_id != "000000000000":
            accounts_to_sync.append("000000000000")

        for acct in accounts_to_sync:
            # Ensure bucket exists in account namespace
            try:
                put_bucket_req = urllib.request.Request(
                    f"{endpoint}/{bucket_name}",
                    method="PUT",
                    headers={
                        "Authorization": f"AWS4-HMAC-SHA256 Credential={acct}/20261106/{context.region}/s3/aws4_request, SignedHeaders=host, Signature=mock"
                    }
                )
                with urllib.request.urlopen(put_bucket_req, timeout=5) as r:
                    pass
            except Exception:
                pass  # Bucket might already exist

            for root, _, files in os.walk(dist_path):
                for f in files:
                    file_path = Path(root) / f
                    rel_path = file_path.relative_to(dist_path).as_posix()
                    ext = file_path.suffix.lower()
                    mime_type = MIME_MAP.get(ext, mimetypes.guess_type(str(file_path))[0] or "application/octet-stream")

                    with open(file_path, "rb") as body_f:
                        data = body_f.read()

                    cache_control = "max-age=31536000, immutable" if rel_path.startswith("assets/") else "no-cache"

                    req = urllib.request.Request(
                        f"{endpoint}/{bucket_name}/{rel_path}",
                        data=data,
                        method="PUT",
                        headers={
                            "Content-Type": mime_type,
                            "Content-Length": str(len(data)),
                            "Cache-Control": cache_control,
                            "Authorization": f"AWS4-HMAC-SHA256 Credential={acct}/20261106/{context.region}/s3/aws4_request, SignedHeaders=content-length;content-type;host, Signature=mock"
                        }
                    )
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        if resp.status not in (200, 204):
                            self.handle_error(
                                PlatformErrorCode.DEPLOYMENT_FAILURE,
                                f"Failed uploading {rel_path} to {bucket_name} (HTTP {resp.status})"
                            )

                    if acct == context.account_id:
                        uploaded.append(rel_path)
                        print(f"  [OK] {rel_path} ({len(data)} bytes, {mime_type})")

        website_url = f"{endpoint}/{bucket_name}/index.html"
        print(f"[{self.adapter_name}] Successfully deployed {len(uploaded)} assets. Website URL: {website_url}")

        return S3DeployResult(
            bucket_name=bucket_name,
            target_platform=context.target_platform,
            uploaded_files=uploaded,
            website_url=website_url
        )
