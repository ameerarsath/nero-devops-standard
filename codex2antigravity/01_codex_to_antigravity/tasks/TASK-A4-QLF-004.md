Message ID: TASK-A4-QLF-004
Task ID: A4-QLF-004
Sender: Codex
Recipient: Antigravity
Message Type: ASSIGNMENT
Timestamp: 2026-11-16T14:27:43.3605524+05:30
Related Message ID: TASK-A4-QLF-003
Current Task Status: ASSIGNED

# NERO Implementation Assignment

Task ID: A4-QLF-004
Task Title: Release Audit Ledger Integrator
Milestone: A4 Phase 4, qualification and audit
Priority: High; begin after QLF-003 result
Authorization ID: NERO-A4-GATE3-20261115-001

## Objective

Append verifiable release lifecycle events to an explicitly chosen isolated ledger, preserving chain integrity, concurrency safety and authoritative ledger baseline.

## Background

Read A4 architecture section 4, QLF-001/002/003 results, `platform_core/audit/audit_logger.py`, `audit_verifier.py`, and `PLAN-A4-PHASES-001`. The legacy logger suppresses some lock acquisition errors and tolerates malformed tails; do not inherit those fail-open semantics. `CORR-ACT-AUDIT-001` remains separate.

## Existing Files to Inspect

`platform_core/audit/audit_logger.py`, `platform_core/audit/audit_verifier.py`, `platform_core/engine/release_qualification.py`, `platform_core/engine/release_fsm.py`, and the authoritative ledger read-only for format/baseline.

## Files Allowed to Modify

`platform_core/audit/release_audit.py` and `tests/unit/test_release_audit.py` only, plus Antigravity-owned protocol replies.

## Files Prohibited from Modification

Authoritative `platform_core/audit/audit_log.jsonl`, existing audit logger/verifier/checkpoints, all other source/tests, Docker/Jenkins/Terraform, Codex files and keys.

## Implementation Requirements

Provide typed `ReleaseAuditEvent` with event ID, release/application IDs, manifest checksum, actor, timestamp, event type (`RELEASE_QUALIFIED`, `RELEASE_REJECTED`, `RELEASE_MINTED`, transition/revocation as applicable), outcome and bounded sanitized detail; `append_release_event(event, ledger_path)` and `verify_release_ledger(ledger_path)` APIs. Require explicit caller-supplied ledger path and reject the authoritative ledger path in this Phase 4 implementation/test use. Hold a cross-process lock for read-last/validate/append; lock failure must error, never continue unlocked. Verify existing chain and event-ID uniqueness before append; fail closed on malformed/truncated tail, mismatched prev hash, duplicate event, or conflicting release/checksum. Deterministic canonical JSON hash compatible with audit verifier, one complete newline-terminated record, flush/fsync before success, monotonic chain linkage. Do not rewrite/truncate previous records or append success events for failed QLF reports. Record failed qualification as `RELEASE_REJECTED` only from an actual failed report. No default path based on cwd. Treat `RELEASE_MINTED` as an event contract only; do not mint/publish a release in this task.

## Security Requirements

No secrets, tokens, private keys or raw scanner payloads in ledger details. Path confinement to caller-owned test root; no symlinked ledger/parent; deny authoritative path. Handle concurrent writers and crash/error injection without claiming a committed event when durable write fails.

## Test Requirements

Temp ledgers only: valid append/verify, chain tamper/malformed tail, duplicate/conflict, lock failure, concurrent append, crash/error injection, audit source unchanged byte-for-byte, no event on failed prerequisite. Run isolated and full regression.

## Acceptance Criteria

Verifiable append-only chain, fail-closed locking and malformed-tail handling, exact event/report linkage, no authoritative ledger write, tests pass.

## Infrastructure Restrictions

No real audit append, cloud, Docker/Jenkins/Terraform mutation, commit or push. Keep authoritative 84-record ledger unchanged during this phase.

## Expected Deliverables

Two allowed files, `ACK-TASK-A4-QLF-004.md`, and `RESULT-TASK-A4-QLF-004.md`.

## Completion Report Requirements

Exact chain/locking contract, commands/counts, failure-injection evidence, source ledger hash, Terraform baseline, changed files, and unresolved risks.

## Stop Conditions

Stop for need to modify existing audit files or real ledger, scope conflict, or baseline drift; ask via Markdown. After QLF-004 result, stop for Codex Phase 4 batch evaluation. Do not begin Phase 5.
