"""
NERO Universal Enterprise DevOps Automation Platform - Deployment Orchestrator Facade (A1-COR-001)

Exposes backward-compatible, centralized orchestration APIs delegating to modular subsystems:
- Release Manager: release creation, promotion, manifest cryptographic validation.
- Deployment Manager: infrastructure planning/applying, container/static deployments, health checks.
- Rollback & Governance Manager: two-person production governance, break-glass deployment, zero-rebuild rollback.
"""

# 1. Release Subsystem
from platform_core.engine.release_manager import (
    build_release,
    validate_release_manifest,
)

# 2. Deployment Subsystem
from platform_core.engine.deployment_manager import (
    get_frontend_bucket,
    plan_infrastructure,
    apply_infrastructure,
    deploy_frontend_assets,
    verify_deployment,
    deploy_container_workload,
)

# 3. Rollback and Governance Subsystem
from platform_core.engine.rollback_manager import (
    record_audit_event,
    record_governance_event,
    record_emergency_governance_event,
    execute_rollback,
)

__all__ = [
    # Release Management
    "build_release",
    "validate_release_manifest",
    # Deployment Management
    "get_frontend_bucket",
    "plan_infrastructure",
    "apply_infrastructure",
    "deploy_frontend_assets",
    "verify_deployment",
    "deploy_container_workload",
    # Rollback & Governance
    "record_audit_event",
    "record_governance_event",
    "record_emergency_governance_event",
    "execute_rollback",
]
