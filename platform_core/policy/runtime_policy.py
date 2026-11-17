"""
Enterprise Universal Application Delivery Platform - Central Runtime Support Policy
Enforces runtime lifecycle support, base image security, and dependency lockfile requirements.
"""

import os
import re
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

from platform_core.engine.errors import PlatformException, PlatformErrorCode, SecurityPolicyError


class RuntimeStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    DEPRECATED = "DEPRECATED"
    PROHIBITED = "PROHIBITED"


class RuntimePolicyError(PlatformException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code=PlatformErrorCode.VALIDATION_ERROR,
            message=f"Runtime Policy Violation: {message}",
            details=details
        )


# Centrally maintained vendor lifecycle policy matrix
RUNTIME_LIFECYCLE_MATRIX: Dict[str, Dict[str, Dict[str, Any]]] = {
    "nodejs": {
        "22": {"status": RuntimeStatus.SUPPORTED, "eol": "2027-04-30", "tier": "Active LTS"},
        "20": {"status": RuntimeStatus.SUPPORTED, "eol": "2026-04-30", "tier": "Maintenance LTS"},
        "24": {"status": RuntimeStatus.SUPPORTED, "eol": "2028-04-30", "tier": "Current"},
        "18": {"status": RuntimeStatus.PROHIBITED, "eol": "2025-04-30", "tier": "End-of-Life"},
        "16": {"status": RuntimeStatus.PROHIBITED, "eol": "2023-09-11", "tier": "End-of-Life"},
    },
    "python": {
        "3.13": {"status": RuntimeStatus.SUPPORTED, "eol": "2029-10-31", "tier": "Active Stable"},
        "3.12": {"status": RuntimeStatus.SUPPORTED, "eol": "2028-10-31", "tier": "Active LTS"},
        "3.11": {"status": RuntimeStatus.SUPPORTED, "eol": "2027-10-31", "tier": "Security Only"},
        "3.10": {"status": RuntimeStatus.DEPRECATED, "eol": "2026-10-31", "tier": "Security Only / Deprecated"},
        "3.9":  {"status": RuntimeStatus.PROHIBITED, "eol": "2025-10-31", "tier": "End-of-Life"},
        "3.8":  {"status": RuntimeStatus.PROHIBITED, "eol": "2024-10-31", "tier": "End-of-Life"},
    },
    "java": {
        "21": {"status": RuntimeStatus.SUPPORTED, "eol": "2028-09-30", "tier": "Active LTS"},
        "17": {"status": RuntimeStatus.SUPPORTED, "eol": "2026-09-30", "tier": "Active LTS"},
        "11": {"status": RuntimeStatus.DEPRECATED, "eol": "2026-09-30", "tier": "Deprecated LTS"},
        "8":  {"status": RuntimeStatus.PROHIBITED, "eol": "2022-03-31", "tier": "End-of-Life"},
    },
    "go": {
        "1.27.3": {"status": RuntimeStatus.SUPPORTED, "eol": "2028-02-28", "tier": "Approved Baseline"},
        "1.27":   {"status": RuntimeStatus.SUPPORTED, "eol": "2028-02-28", "tier": "Approved Baseline"},
        "1.24":   {"status": RuntimeStatus.SUPPORTED, "eol": "2026-02-28", "tier": "Current"},
        "1.23":   {"status": RuntimeStatus.SUPPORTED, "eol": "2025-08-31", "tier": "Maintenance"},
        "1.22":   {"status": RuntimeStatus.PROHIBITED, "eol": "2025-02-28", "tier": "End-of-Life"},
    }
}


class RuntimeComplianceResult(BaseModel):
    component_name: str
    runtime_name: str
    runtime_version: str
    status: RuntimeStatus
    base_image: str
    lockfile_path: Optional[str] = None
    lockfile_valid: bool = False
    message: str = ""


class RuntimePolicyValidator:
    """
    Centrally validates that every component adheres to enterprise runtime policies.
    """

    @staticmethod
    def inspect_dockerfile(dockerfile_path: Path) -> Tuple[Optional[str], Optional[str], str]:
        """
        Extracts runtime name, version, and full base image string from Dockerfile.
        """
        if not dockerfile_path.is_file():
            return None, None, ""

        with open(dockerfile_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line.upper().startswith("FROM "):
                    parts = line.split()
                    if len(parts) >= 2:
                        base = parts[1]
                        # match node:22-alpine, python:3.12-slim, eclipse-temurin:17-jre, maven:3.9-eclipse-temurin-17
                        if "node" in base:
                            v_match = re.search(r"node:([0-9]+)", base)
                            v = v_match.group(1) if v_match else "unknown"
                            return "nodejs", v, base
                        elif "python" in base:
                            v_match = re.search(r"python:([0-9]+\.[0-9]+)", base)
                            v = v_match.group(1) if v_match else "unknown"
                            return "python", v, base
                        elif "eclipse-temurin" in base or "openjdk" in base or "maven" in base:
                            v_match = re.search(r"temurin-([0-9]+)|openjdk:([0-9]+)|java:([0-9]+)", base)
                            v = next((g for g in v_match.groups() if g), "unknown") if v_match else "17"
                            return "java", v, base
                        elif "golang" in base:
                            v_match = re.search(r"golang:([0-9]+\.[0-9]+(?:\.[0-9]+)?)", base)
                            v = v_match.group(1) if v_match else "1.27.3"
                            return "go", v, base
                        elif "distroless" in base:
                            return "go", "1.27.3", base
                        return "generic", "unknown", base
        return None, None, ""

    @classmethod
    def validate_component(
        cls,
        component_data: Dict[str, Any],
        context_dir: Path
    ) -> RuntimeComplianceResult:
        comp_name = component_data.get("name", "unknown")
        src = component_data.get("source", {})
        df_rel = src.get("dockerfile", "Dockerfile")
        df_path = context_dir / df_rel

        detected_runtime, detected_version, base_image = cls.inspect_dockerfile(df_path)

        if not detected_runtime:
            # Check build adapter
            adapter = component_data.get("build", {}).get("adapter", "")
            if "node" in adapter:
                detected_runtime = "nodejs"
                detected_version = "22"
                base_image = "node:22-alpine"
            elif adapter in ("go", "golang") or component_data.get("runtime", {}).get("name") == "go":
                detected_runtime = "go"
                detected_version = component_data.get("runtime", {}).get("version", "1.27.3")
                base_image = "gcr.io/distroless/static-debian12:nonroot"
            else:
                detected_runtime = "generic"
                detected_version = "unknown"
                base_image = "scratch"

        # Check policy
        status = RuntimeStatus.SUPPORTED
        msg = f"Runtime {detected_runtime} {detected_version} is compliant"

        runtime_policy = RUNTIME_LIFECYCLE_MATRIX.get(detected_runtime, {})
        if detected_version in runtime_policy:
            pol = runtime_policy[detected_version]
            status = pol["status"]
            if status == RuntimeStatus.PROHIBITED:
                raise RuntimePolicyError(
                    f"Component '{comp_name}' uses prohibited/EOL runtime {detected_runtime}:{detected_version} (EOL: {pol['eol']}). Must upgrade to a supported LTS version.",
                    details={"component": comp_name, "runtime": detected_runtime, "version": detected_version, "policy": pol}
                )
            elif status == RuntimeStatus.DEPRECATED:
                msg = f"Component '{comp_name}' uses deprecated runtime {detected_runtime}:{detected_version}. Consider upgrading to current LTS."
        elif detected_runtime in RUNTIME_LIFECYCLE_MATRIX and detected_version not in ("unknown", ""):
            # Prohibit versions older than lowest listed or unknown major versions
            raise RuntimePolicyError(
                f"Component '{comp_name}' uses unapproved runtime version {detected_runtime}:{detected_version}.",
                details={"component": comp_name, "runtime": detected_runtime, "version": detected_version}
            )

        # Validate lockfile presence
        lockfile_path = None
        lockfile_valid = False
        if detected_runtime == "nodejs":
            lock_candidates = [context_dir / "package-lock.json", context_dir / "yarn.lock", context_dir / "pnpm-lock.yaml"]
            for lc in lock_candidates:
                if lc.is_file():
                    lockfile_path = str(lc)
                    lockfile_valid = True
                    break
            if not lockfile_valid:
                raise RuntimePolicyError(
                    f"Component '{comp_name}' is missing dependency lockfile (package-lock.json). Unreproducible builds are prohibited.",
                    details={"component": comp_name, "expected": "package-lock.json"}
                )
        elif detected_runtime == "python":
            lock_candidates = [context_dir / "requirements.txt", context_dir / "Pipfile.lock", context_dir / "poetry.lock"]
            for lc in lock_candidates:
                if lc.is_file():
                    lockfile_path = str(lc)
                    lockfile_valid = True
                    break
        elif detected_runtime == "java":
            lock_candidates = [context_dir / "pom.xml", context_dir / "build.gradle"]
            for lc in lock_candidates:
                if lc.is_file():
                    lockfile_path = str(lc)
                    lockfile_valid = True
                    break
        elif detected_runtime == "go":
            lock_candidates = [context_dir / "go.sum", context_dir / "go.mod"]
            for lc in lock_candidates:
                if lc.is_file():
                    lockfile_path = str(lc)
                    lockfile_valid = True
                    break

        return RuntimeComplianceResult(
            component_name=comp_name,
            runtime_name=detected_runtime,
            runtime_version=detected_version,
            status=status,
            base_image=base_image,
            lockfile_path=lockfile_path,
            lockfile_valid=lockfile_valid,
            message=msg
        )

    @classmethod
    def enforce_non_root_policy(cls, dockerfile_path: Path, component_name: str = "") -> None:
        """
        Enforces non-root execution policy programmatically across application components (A1-SEC-001).
        Raises SecurityPolicyError (Exit Code 20) if root execution is detected.
        """
        compliant, reason, user = check_dockerfile_non_root(dockerfile_path)
        if not compliant:
            raise SecurityPolicyError(
                f"Component '{component_name}' Dockerfile security violation: {reason}. "
                "Enterprise security baseline requires non-root execution (UID != 0).",
                details={"dockerfile": str(dockerfile_path), "reason": reason, "user": user}
            )


def check_dockerfile_non_root(dockerfile_path: Path) -> Tuple[bool, str, Optional[str]]:
    """
    Parses a Dockerfile instruction AST to verify that the final execution stage
    declares an explicit non-root USER directive (A1-SEC-001).
    Returns (is_compliant, reason_message, detected_user).
    """
    if not dockerfile_path.is_file():
        return True, "No Dockerfile found", None

    stages: List[List[Tuple[str, str]]] = []
    current_stage: List[Tuple[str, str]] = []

    with open(dockerfile_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(None, 1)
            inst = parts[0].upper()
            val = parts[1].strip() if len(parts) > 1 else ""

            if inst == "FROM":
                if current_stage:
                    stages.append(current_stage)
                current_stage = [(inst, val)]
            else:
                current_stage.append((inst, val))

    if current_stage:
        stages.append(current_stage)

    if not stages:
        return False, "Empty Dockerfile", None

    # Inspect the final execution stage
    final_stage = stages[-1]
    final_user = None

    for inst, val in final_stage:
        if inst == "USER":
            final_user = val

    if not final_user:
        return False, "Missing explicit non-root USER directive in final stage (runs as root/UID 0)", None

    user_part = final_user.split(":")[0].strip()
    if user_part in ("0", "root"):
        return False, f"Prohibited root USER directive declared: '{final_user}'", final_user

    return True, f"Compliant non-root USER directive: '{final_user}'", final_user

