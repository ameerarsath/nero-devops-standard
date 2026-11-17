Message ID: TASK-A4-QLF-002
Task ID: A4-QLF-002
Sender: Codex
Recipient: Antigravity
Message Type: ASSIGNMENT
Timestamp: 2026-11-16T14:27:43.3605524+05:30
Related Message ID: TASK-A4-QLF-001
Current Task Status: ASSIGNED

# NERO Implementation Assignment

Task ID: A4-QLF-002
Task Title: Release Finite State Machine
Milestone: A4 Phase 4, qualification and audit
Priority: High; begin after QLF-001 result
Authorization ID: NERO-A4-GATE3-20261115-001

## Objective

Enforce legal release lifecycle transitions with explicit authorization/evidence guards and deterministic rejection of skips or terminal-state escape.

## Background

Read the A4 architecture section 4 state diagram, `PLAN-A4-PHASES-001`, QLF-001 result, and `ReleaseQualification` model. The lifecycle state is separate from the manifest's environment qualification state.

## Existing Files to Inspect

`platform_core/engine/release_qualification.py`, `platform_core/models/release_manifest_v2.py`, and A4 architecture/governance records.

## Files Allowed to Modify

`platform_core/engine/release_fsm.py` and `tests/unit/test_release_fsm.py` only, plus Antigravity-owned protocol replies.

## Files Prohibited from Modification

All other source/tests, manifest/catalog data, audit ledger, application source, Docker/Jenkins/Terraform, Codex files and keys.

## Implementation Requirements

Expose typed states `CANDIDATE`, `QUALIFIED`, `REJECTED`, `PROMOTION_PENDING`, `PROMOTED`, `SUPERSEDED`, `REVOKED`; typed transition request/result; pure `transition(current, event, context)` API. Legal edges: CANDIDATE->QUALIFIED only with passing QLF-001 report for same release ID/checksum; CANDIDATE->REJECTED on failed report; QUALIFIED->PROMOTION_PENDING with target; PROMOTION_PENDING->PROMOTED only with required target authorization and digest parity; PROMOTED->PROMOTION_PENDING for next legal environment; PROMOTED->SUPERSEDED on replacement; any eligible nonterminal state->REVOKED on validated security revocation. REJECTED and REVOKED are terminal. No direct CANDIDATE->PROMOTED or self-approval inference. Reject cross-release reports, stale state/version, duplicate event replay, backward/skip promotion, and target mismatch. Keep transition result immutable and serializable; no persistence or audit side effects. If approved architecture conflicts with these edges, publish a question before coding that edge.

## Security Requirements

Fail closed on missing report, unqualified release, missing governance proof, revoked source, or digest mismatch. Do not treat a free-form requester string as authenticated production approval; production promotion remains denied until Phase 5 supplies that boundary.

## Test Requirements

Full legal/illegal edge matrix, terminal-state denial, duplicate replay, version/CAS conflict, cross-release report, missing approval and digest evidence. Run isolated FSM and QLF-001 plus existing regression.

## Acceptance Criteria

All legal transitions deterministic; every illegal, stale, or unproven transition denied without state mutation; tests pass.

## Infrastructure Restrictions

Pure local in-memory tests; no ledger append, cloud, Docker/Jenkins/Terraform mutation, commit or push.

## Expected Deliverables

Two allowed files, `ACK-TASK-A4-QLF-002.md`, and `RESULT-TASK-A4-QLF-002.md`.

## Completion Report Requirements

Transition table, API, tests/counts, file inventory, preserved baselines and any unresolved governance limits.

## Stop Conditions

Publish result before QLF-003. Ask via protocol for architecture/scope ambiguity. Do not begin Phase 5.
