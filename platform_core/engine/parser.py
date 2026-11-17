"""
NERO Universal Enterprise DevOps Automation Platform - Application Spec Parser
Performs multi-layered verification:
1. File size and safe YAML parsing (prevents Billion Laughs & DoS)
2. Backward compatibility engine (v1 -> v2 automatic normalization)
3. JSON Schema Draft 2020-12 structural validation
4. Pydantic v2 strong-typing and deep constraint verification
5. Physical path traversal and symlink confinement verification
(A2-SCH-003, A2-SCH-004)
"""

import os
import json
import yaml
import jsonschema
from typing import Dict, Any, Optional
from pathlib import Path

from platform_core.engine.models import ApplicationSpec
from platform_core.engine.errors import SpecValidationError

MAX_SPEC_FILE_BYTES = 512 * 1024  # 512 KB max file size
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "catalog" / "schema" / "app_spec_schema.json"


def load_json_schema() -> Dict[str, Any]:
    if not SCHEMA_PATH.is_file():
        raise SpecValidationError(f"Platform JSON Schema not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_and_migrate_spec(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Backward Compatibility Engine (A2-SCH-003).
    Normalizes legacy v1 or platform.nero/v1 specifications into modern ApplicationSpec format.
    """
    if not isinstance(raw_data, dict):
        return raw_data

    normalized = dict(raw_data)
    api_version = normalized.get("apiVersion", "platform.enterprise.com/v1")

    # If v1 metadata is present without explicit id, inherit id from name
    metadata = normalized.get("metadata", {})
    if isinstance(metadata, dict):
        if "id" not in metadata and "name" in metadata:
            metadata["id"] = metadata["name"]
        if "securityTier" not in metadata:
            metadata["securityTier"] = "tier-2-standard"
        normalized["metadata"] = metadata

    return normalized


def parse_and_validate_spec(file_path: str, workspace_root: Optional[str] = None) -> ApplicationSpec:
    """
    Parses and validates an application specification from disk.
    
    Args:
        file_path: Absolute or relative path to app.spec.yaml
        workspace_root: Optional root directory to enforce filesystem containment
        
    Returns:
        Validated ApplicationSpec model
        
    Raises:
        SpecValidationError on any structural, type, or security violation
    """
    path = Path(file_path).resolve()
    if not path.is_file():
        raise SpecValidationError(f"Application specification not found: {file_path}")

    # Guard 1: File size limit to prevent memory exhaustion
    file_size = path.stat().st_size
    if file_size > MAX_SPEC_FILE_BYTES:
        raise SpecValidationError(
            f"Specification file size ({file_size} bytes) exceeds platform maximum of {MAX_SPEC_FILE_BYTES} bytes"
        )

    # Guard 2: Safe YAML parsing
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise SpecValidationError(f"Invalid YAML syntax in application specification: {e}")

    if not isinstance(raw_data, dict):
        raise SpecValidationError("Application specification root must be a YAML dictionary")

    # Guard 3: Backward compatibility normalization (A2-SCH-003)
    raw_data = normalize_and_migrate_spec(raw_data)

    # Guard 4: JSON Schema structural validation
    schema = load_json_schema()
    try:
        validator = jsonschema.Draft202012Validator(schema)
        errors = list(validator.iter_errors(raw_data))
        if errors:
            first_err = errors[0]
            err_path = " -> ".join(str(p) for p in first_err.absolute_path) or "root"
            raise SpecValidationError(
                f"JSON Schema validation error at [{err_path}]: {first_err.message}",
                details={"errors": [e.message for e in errors[:5]]}
            )
    except jsonschema.exceptions.SchemaError as e:
        raise SpecValidationError(f"Internal platform schema error: {e}")

    # Guard 5: Pydantic v2 strong-typing and deep semantic validation
    try:
        validated_spec = ApplicationSpec.model_validate(raw_data)
    except Exception as e:
        raise SpecValidationError(f"Application specification constraint violation: {e}")

    # Guard 6: Physical path & filesystem confinement check (A2-SCH-004)
    if workspace_root:
        ws_path = Path(workspace_root).resolve()
        for comp in validated_spec.spec.components:
            comp_context = (ws_path / comp.source.context).resolve()
            
            # Ensure context is strictly within workspace_root (anti-traversal)
            try:
                comp_context.relative_to(ws_path)
            except ValueError:
                raise SpecValidationError(
                    f"Component '{comp.name}' source context '{comp.source.context}' escapes workspace root {workspace_root}"
                )

            if not comp_context.is_dir():
                raise SpecValidationError(
                    f"Component '{comp.name}' source context directory not found: {comp.source.context}"
                )

            # Check Dockerfile confinement if declared
            if comp.source.dockerfile:
                df_path = (comp_context / comp.source.dockerfile).resolve()
                try:
                    df_path.relative_to(comp_context)
                except ValueError:
                    raise SpecValidationError(
                        f"Component '{comp.name}' Dockerfile path escapes component context: {comp.source.dockerfile}"
                    )
                if not df_path.is_file():
                    raise SpecValidationError(
                        f"Component '{comp.name}' Dockerfile not found at: {comp.source.context}/{comp.source.dockerfile}"
                    )

            # Check dist_dir confinement if static site
            if comp.type == "static-site" and comp.build.dist_dir:
                dist_path = (comp_context / comp.build.dist_dir).resolve()
                try:
                    dist_path.relative_to(comp_context)
                except ValueError:
                    raise SpecValidationError(
                        f"Component '{comp.name}' build.dist_dir escapes component context: {comp.build.dist_dir}"
                    )

    return validated_spec


def inspect_spec_capabilities(spec: ApplicationSpec) -> Dict[str, Any]:
    """
    Extracts summary capability metadata to drive universal Jenkins pipeline dispatch
    without application-specific hardcoded branching.
    """
    container_comps = [c for c in spec.spec.components if c.type in ("container-service", "worker", "scheduled-task")]
    frontend_comps = [c for c in spec.spec.components if c.type == "static-site"]
    worker_comps = [c for c in spec.spec.components if c.type == "worker"]

    has_infra = bool(spec.spec.dependencies and len(spec.spec.dependencies) > 0)

    return {
        "app_id": spec.metadata.id or spec.metadata.name,
        "version": spec.metadata.version,
        "has_container": len(container_comps) > 0,
        "has_frontend": len(frontend_comps) > 0,
        "has_worker": len(worker_comps) > 0,
        "has_infra": has_infra,
        "container_components": [c.name for c in container_comps],
        "frontend_components": [c.name for c in frontend_comps],
        "worker_components": [c.name for c in worker_comps],
        "dependencies": [d.name for d in (spec.spec.dependencies or [])]
    }
