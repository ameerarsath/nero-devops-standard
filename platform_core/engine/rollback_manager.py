"""
NERO Universal Enterprise DevOps Automation Platform - Rollback & Governance Manager (A1-COR-001)
Responsible for staged instant rollbacks, two-person governance enforcement, and emergency break-glass deployments.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

from platform_core.engine.errors import ConfigurationError, GovernancePolicyError
from platform_core.audit.audit_logger import append_audit_record


def record_audit_event(
    workspace_root: str,
    app_id: str,
    environment: str,
    target_platform: str,
    account_topology: str,
    action: str,
    status: str,
    details: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Appends an audit event to the cryptographic audit ledger via the atomic audit logger.
    """
    return append_audit_record(
        workspace_root=workspace_root,
        app_id=app_id,
        environment=environment,
        target_platform=target_platform,
        account_topology=account_topology,
        action=action,
        status=status,
        details=details
    )


def record_governance_event(
    workspace_root: str,
    app_id: str,
    environment: str,
    requester: str,
    qa_approver: str,
    ops_approver: str,
    change_ticket_id: str,
    release_id: Optional[str] = None
):
    """
    Records a production governance approval event binding distinct approver identities,
    change ticket ID, and release identifiers into the audit ledger (A1-AUD-002).
    """
    # Enforce three-party separation of duties
    if not change_ticket_id or not change_ticket_id.startswith("CHG-"):
        raise ConfigurationError(
            f"Governance violation: Invalid change ticket format '{change_ticket_id}'. Must start with 'CHG-'"
        )
    if qa_approver.lower().strip() == ops_approver.lower().strip():
        raise ConfigurationError(
            f"Governance separation of duties violation: QA Approver and Ops Approver cannot be identical ({qa_approver})"
        )
    if requester and (requester.lower().strip() == qa_approver.lower().strip() or requester.lower().strip() == ops_approver.lower().strip()):
        raise ConfigurationError(
            f"Governance separation of duties violation: Requester '{requester}' cannot approve their own release"
        )

    record_audit_event(
        workspace_root=workspace_root,
        app_id=app_id,
        environment=environment,
        target_platform="floci",
        account_topology="multi_account",
        action="GOVERNANCE_TWO_PERSON_APPROVAL",
        status="APPROVED",
        details={
            "requester": requester,
            "gate1_qa_approver": qa_approver,
            "gate2_ops_approver": ops_approver,
            "change_ticket_id": change_ticket_id,
            "release_id": release_id or "latest",
            "approval_timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


def record_emergency_governance_event(
    workspace_root: str,
    app_id: str,
    environment: str,
    requester: str,
    incident_commander: str,
    emergency_approver: str,
    secops_approver: str,
    incident_ticket_id: str,
    release_id: str
) -> Dict[str, Any]:
    """
    Records an emergency break-glass deployment governance event.
    Requires 4 distinct roles and a valid INC-* or HOTFIX-* ticket reference.
    Strictly verifies that release_id references an existing, valid immutable release.
    """
    if not incident_ticket_id or not (incident_ticket_id.startswith("INC-") or incident_ticket_id.startswith("HOTFIX-")):
        raise ConfigurationError(
            f"Emergency governance violation: Invalid incident ticket format '{incident_ticket_id}'. Must start with 'INC-' or 'HOTFIX-'"
        )

    actors = [
        requester.lower().strip(),
        incident_commander.lower().strip(),
        emergency_approver.lower().strip(),
        secops_approver.lower().strip()
    ]
    if len(set(actors)) != 4:
        raise ConfigurationError(
            f"Emergency governance violation: All 4 emergency roles must be distinct identities (Found: requester={requester}, ic={incident_commander}, emergency={emergency_approver}, secops={secops_approver})"
        )

    # Strictly verify that release manifest exists and is cryptographically intact
    manifest_path = Path(workspace_root) / "platform_core" / "manifests" / f"{release_id}.json"
    if not manifest_path.is_file():
        raise ConfigurationError(
            f"Emergency governance violation: Release manifest for '{release_id}' not found in platform_core/manifests. Direct deployment of unverified artifacts is strictly prohibited."
        )

    from platform_core.engine.release_manager import validate_release_manifest
    validated_manifest = validate_release_manifest(
        manifest_path=str(manifest_path.relative_to(Path(workspace_root))),
        expected_app_id=app_id,
        workspace_root=workspace_root
    )

    record_audit_event(
        workspace_root=workspace_root,
        app_id=app_id,
        environment=environment,
        target_platform="floci",
        account_topology="multi_account",
        action="EMERGENCY_BREAK_GLASS_DEPLOYMENT",
        status="APPROVED",
        details={
            "requester": requester,
            "incident_commander": incident_commander,
            "emergency_approver": emergency_approver,
            "secops_approver": secops_approver,
            "incident_ticket_id": incident_ticket_id,
            "release_id": release_id,
            "approval_timestamp": datetime.now(timezone.utc).isoformat()
        }
    )
    return validated_manifest


def execute_rollback(
    workspace_root: str,
    app_id: str,
    environment: str,
    target_release_id: str,
    operator: str,
    reason: str,
    ticket_id: str
) -> Dict[str, Any]:
    """
    Dedicated rollback operation that retrieves, cryptographically validates,
    and deploys a previous immutable release manifest with zero recompilation.
    """
    if not ticket_id or not any(ticket_id.startswith(p) for p in ("CHG-", "INC-", "HOTFIX-", "ROLLBACK-")):
        raise ConfigurationError(
            f"Rollback violation: Invalid ticket format '{ticket_id}'. Must start with 'CHG-', 'INC-', 'HOTFIX-', or 'ROLLBACK-'"
        )

    manifest_path = Path(workspace_root) / "platform_core" / "manifests" / f"{target_release_id}.json"
    if not manifest_path.is_file():
        raise ConfigurationError(f"Rollback failed: Previous release manifest '{target_release_id}.json' not found")

    from platform_core.engine.release_manager import validate_release_manifest
    manifest = validate_release_manifest(
        manifest_path=str(manifest_path.relative_to(Path(workspace_root))),
        expected_app_id=app_id,
        workspace_root=workspace_root
    )

    # Set as active release manifest
    active_manifest_path = Path(workspace_root) / "release-manifest.json"
    with open(active_manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    record_audit_event(
        workspace_root=workspace_root,
        app_id=app_id,
        environment=environment,
        target_platform="floci",
        account_topology="multi_account",
        action="PRODUCTION_ROLLBACK",
        status="EXECUTED",
        details={
            "operator": operator,
            "reason": reason,
            "ticket_id": ticket_id,
            "target_release_id": target_release_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )
    print(f"[ROLLBACK] Successfully validated and staged previous immutable release '{target_release_id}' (Zero Rebuild)")
    return manifest
