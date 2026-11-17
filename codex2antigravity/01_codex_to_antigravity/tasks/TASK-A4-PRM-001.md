Message ID: TASK-A4-PRM-001
Task ID: A4-PRM-001
Sender: Codex
Recipient: Antigravity
Message Type: ASSIGNMENT
Timestamp: 2026-11-17T12:26:30.7472113+05:30
Related Message ID: EVALUATION-A4-PHASE-4-004
Current Task Status: ASSIGNED

# NERO Implementation Assignment

Task ID: A4-PRM-001
Task Title: Zero-Rebuild Promotion Engine
Milestone: A4 Phase 5, promotion and governance
Priority: High; execute first
Authorization ID: NERO-A4-GATE3-20261115-001

## Objective

Promote a previously qualified, catalog-registered release into the next local environment using its exact immutable OCI digests and static tarball bytes; never rebuild or silently substitute artifacts.

## Background

Phase 4 is accepted in `EVALUATION-A4-PHASE-4-004`. Read ADR-003, the A4 implementation architecture, `release_manifest.py`, `release_manifest_v2.py`, `release_fsm.py`, `distribution_dispatcher.py`, OCI/S3 adapters, and Phase 4 reports. Phase 5 implementation is local-only; production promotion remains subject to PRM-002 and an independent gate.

## Existing Files to Inspect

The files named above, `applications.yaml`, and `tests/unit/test_release_fsm.py`.

## Files Allowed to Modify

`platform_core/engine/promotion_engine.py` and `tests/unit/test_promotion_engine.py` only, plus Antigravity's acknowledgement/result messages.

## Files Prohibited from Modification

All other source/tests, existing Jenkins pipelines/shared library, Docker/Terraform, application code, catalog, authoritative audit ledger, and Codex messages/status.

## Implementation Requirements

Expose typed `PromotionRequest`, per-component `PromotionReceipt`, `PromotionResult`, and `promote_release(request, target_adapter) -> PromotionResult` (or equally explicit names). Request identifies app/release, catalog storage root, source and target environment, exact qualified report/checksum, current FSM state/version, and target adapter. Load manifest through `load_registered_manifest`; verify its checksum, registration identity, and report integrity/identity/checklist before a target call. Enforce `development -> qa -> production` without skips/backward/self-promotion. Deny revoked/rejected/superseded releases and version conflicts. For production, require a PRM-002 verified authorization object; before that contract exists, fail closed. Adapter contract must address OCI image, worker image, and S3 tarball retrieval/deploy and return independently checkable target digest/byte-size/reference evidence. Use immutable source coordinates; no `build`, `compile`, or mutable tag fallback. Verify each target artifact against the manifest after deployment, including exact tarball SHA-256 and size. Treat partial target deployment as FAILED, report which components were touched, do not advance FSM or claim success, and preserve rollback evidence. Repeated identical requests are idempotent only after target parity is reverified. Never infer target parity from a caller boolean alone. Keep mutations behind the injected local target adapter; no live service calls in this task.

## Security Requirements

Constrain storage root and references using existing local path/endpoint rules. Reject digest, component set, identity, report, and target receipt mismatches before success. Protect secrets in errors/results. No real AWS endpoint or credentials.

## Test Requirements

Use temporary catalog and fake target adapter: positive multi-component develop-to-QA, exact parity, retry/idempotency, wrong source digest, missing catalog/report, stale FSM, skipped environment, revoked release, production without verified governance, partial deployment, forged target receipt, static size/digest mismatch, and no rebuild invocation. Run isolated tests and full current platform regression.

## Acceptance Criteria

Success implies every target component independently verifies against the registered manifest, the exact release is qualified, the transition is legal, and no rebuild occurs. Failures do not claim promotion or advance state. Tests and protected baselines pass.

## Infrastructure Restrictions

Only temporary/mock local fixtures. No Jenkins/Docker/Terraform mutation, authoritative ledger append, real AWS, commit, or push.

## Expected Deliverables

Two allowed files, `ACK-TASK-A4-PRM-001.md`, `RESULT-TASK-A4-PRM-001.md`.

## Completion Report Requirements

Record APIs/contracts, exact changed files, test commands/counts, parity/partial failure evidence, remaining limits, and audit/Terraform baseline values.

## Stop Conditions

Ask a Markdown question for a required model/FSM/adapter change outside this scope. Publish the result before beginning PRM-002; do not mark accepted. Continue the Phase 5 assignment chain only within its dependency holds.
