Message ID: TASK-A4-PRM-004
Task ID: A4-PRM-004
Sender: Codex
Recipient: Antigravity
Message Type: ASSIGNMENT
Timestamp: 2026-11-17T12:26:30.8739580+05:30
Related Message ID: TASK-A4-PRM-003
Current Task Status: ASSIGNED

# NERO Implementation Assignment

Task ID: A4-PRM-004
Task Title: Trusted Shared Library Release Steps
Milestone: A4 Phase 5, promotion and governance
Priority: High; start after PRM-003 result
Authorization ID: NERO-A4-GATE3-20261115-001

## Objective

Provide reusable trusted Jenkins release steps and connect the new release pipeline to them with fail-closed error propagation.

## Background

Read PRM-001 through PRM-003 results, the A4 architecture, `neroCI.groovy`, shared-library README, `Jenkinsfile.release`, and release CLI. Preserve the existing CI library and jobs.

## Existing Files to Inspect

`ci-cd/jenkins/shared-library/vars/neroCI.groovy`, `ci-cd/jenkins/shared-library/README.md`, `ci-cd/jenkins/pipelines/release/Jenkinsfile.release`, `platform_core/engine/release_cli.py`, PRM-001/002 contracts.

## Files Allowed to Modify

`ci-cd/jenkins/shared-library/vars/neroRelease.groovy` (new), `tests/unit/test_nero_release_shared_library.py` (new), and the new PRM-003 files `ci-cd/jenkins/pipelines/release/Jenkinsfile.release`, `tests/unit/test_release_jenkinsfile.py`, `platform_core/engine/release_cli.py`, `tests/unit/test_release_cli.py` solely for integration and tests. Plus Antigravity's acknowledgement/result messages.

## Files Prohibited from Modification

Existing CI/universal/prod Jenkinsfiles, `neroCI.groovy`, Jenkins job/config, Docker/Terraform, app code, catalog, authoritative ledger, other source/tests, Codex messages/status.

## Implementation Requirements

Expose separate trusted steps for validating the registered release, qualification/security/supply-chain evidence, verifying immutable distribution, evaluating the PRM-002 production gate, and promoting through PRM-001. Each wrapper accepts a small allowlisted parameter map, validates names and local paths, calls the real PRM-003 CLI/modules, and propagates nonzero exits or exceptions. Avoid interpolating raw parameters into shell scripts; use environment binding or properly escaped fixed arguments. `Jenkinsfile.release` must call these steps in the approved order, never build/recompile artifacts, never convert an error into a passing stage, and never bypass production identity/ticket checks. Keep CPS-safe Groovy boundaries: serializable step inputs/outputs, no long-lived Jenkins handles in closures, and no unapproved library revision selection. Clearly distinguish a local simulation from a verified production approval. Keep all active existing pipeline files byte-identical.

## Security Requirements

Reject arbitrary commands/paths/endpoints, mutable tags, cross-release evidence, unverified identity/ticket objects, missing evidence, and secret-bearing logs. No live production promotion. Use only local endpoints.

## Test Requirements

Run Groovy syntax/Jenkins Declarative and shared-library CPS checks with available local tools, plus targeted fake-step tests for command order and failure propagation. Include negative self-approval, invalid ticket, missing qualification, wrong digest, shell metacharacter/path escape, and simulated identity cases. Run full platform regression. If host tooling lacks real CPS validation, explicitly report the unqualified boundary; do not substitute static grep for live proof.

## Acceptance Criteria

The new pipeline and library invoke real fail-closed release checks in order; failure blocks promotion; no rebuild path exists; production is denied without verified PRM-002 authorization; tests pass and existing files/baselines remain unchanged. Report live Jenkins limitations truthfully.

## Infrastructure Restrictions

Read-only local Jenkins validation is allowed. No job/config mutation, live deploy, authoritative audit append, Docker/Terraform mutation, real AWS, commit, or push. Request a scoped assignment for any live local qualification beyond these boundaries.

## Expected Deliverables

Allowed new/integration files, `ACK-TASK-A4-PRM-004.md`, `RESULT-TASK-A4-PRM-004.md`, and one consolidated Phase 5 evidence summary in the latter report.

## Completion Report Requirements

State exact file changes, stage/library contracts, test commands/counts, syntax/CPS evidence or limits, local service availability, risks, and protected baselines. Report implementation completion, not acceptance.

## Stop Conditions

Start only after PRM-003 result. Stop and ask for any required prohibited edit or genuine production identity path. After PRM-004 result, stop for Codex Phase 5 independent evaluation. Do not begin Phase 6.
