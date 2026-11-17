Message ID: TASK-A4-PRM-002
Task ID: A4-PRM-002
Sender: Codex
Recipient: Antigravity
Message Type: ASSIGNMENT
Timestamp: 2026-11-17T12:26:30.8473878+05:30
Related Message ID: TASK-A4-PRM-001
Current Task Status: ASSIGNED

# NERO Implementation Assignment

Task ID: A4-PRM-002
Task Title: Two-Person Production Governance Gate
Milestone: A4 Phase 5, promotion and governance
Priority: High; start after PRM-001 result
Authorization ID: NERO-A4-GATE3-20261115-001

## Objective

Provide a typed fail-closed production authorization decision tied to one release, manifest checksum, target environment, two distinct authenticated people, and an approved active `CHG-*` ticket.

## Background

Read ADR-005, the A4 architecture, `PLAN-A4-PHASES-001`, Phase 4 acceptance, PRM-001 result, and existing Jenkins governance patterns. The local lab demonstrates policy logic; it does not establish enterprise SSO/MFA or independent human identity by free-form strings.

## Existing Files to Inspect

`platform_core/engine/promotion_engine.py`, `release_fsm.py`, `release_qualification.py`, existing Jenkins production pipeline, and ADR-005.

## Files Allowed to Modify

`platform_core/policy/two_person_gate.py` and `tests/unit/test_two_person_gate.py`; also `platform_core/engine/promotion_engine.py` and `tests/unit/test_promotion_engine.py` solely to integrate the typed governance decision into PRM-001's production gate. Plus Antigravity's acknowledgement/result messages.

## Files Prohibited from Modification

All other source/tests, Jenkins, Docker/Terraform, application code, catalogs, authoritative audit ledger, Codex messages/status.

## Implementation Requirements

Expose typed `ApprovalPrincipal`, `ChangeTicketEvidence`, `ProductionApprovalRequest`, `ProductionApprovalDecision`, and `evaluate_production_approval(request, identity_verifier, ticket_verifier)`. Bind both approvals and ticket to exact app/release/manifest checksum and production target, with timestamps, roles, source, verifier identity, and expiry. Verify QA technical approver and SRE/operations approver as required by ADR-005; require them to be distinct independently authenticated principals, and prevent the final SRE approver from approving their own request. Explicitly identify and test the exact separation rule. Require active ticket ID `CHG-...`, `APPROVED` status, correct release scope, and current window. No caller supplied `verified=True` flag or free-form Jenkins form text may establish authentication or ticket validity. If the local verifier only simulates identity, return `LOCAL_APPROVAL_SIMULATION` and deny production authorization. Denials include stable reason codes but no secret material. A successful decision must be consumed and checked by PRM-001 without ambiguous identity or checksum binding. Restrict any PRM-001 edits to this integration and its tests.

## Security Requirements

Reject same principal under case/alias normalization, role mismatch, replay/expired approval, stale ticket, forged verifier result, and cross-release reuse. Never label a local mock as enterprise dual control. No external IdP or ticket-system call in this task.

## Test Requirements

Use injected fake verifiers and isolated data. Test valid verified distinct approvals, self-approval, duplicate QA/SRE, forged free-form strings, wrong role, missing/stale/rejected ticket, mismatched release/checksum, replay/expiry, simulation denial, and immutable decision serialization. Run isolated and full regression.

## Acceptance Criteria

Only independently verified, distinct, in-scope and current principals plus an approved active matching ticket can authorize production; local simulation is clearly reported and cannot authorize. Tests/baselines pass.

## Infrastructure Restrictions

No Jenkins config/job changes, network calls, real AWS, ledger append, Docker/Terraform mutation, commit, or push.

## Expected Deliverables

Two governance files and, only if integration needs them, the two PRM-001 files; `ACK-TASK-A4-PRM-002.md`, `RESULT-TASK-A4-PRM-002.md`.

## Completion Report Requirements

Document trust assumptions, exact decision contract, negative evidence, tests, changed files, and protected baselines.

## Stop Conditions

Start only after PRM-001 result. Stop and ask through Markdown if genuine authenticated identity/ticket proof cannot be represented without out-of-scope changes; never weaken the gate. Publish result before PRM-003.
