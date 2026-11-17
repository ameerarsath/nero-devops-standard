Message ID: TASK-A4-QLF-001
Task ID: A4-QLF-001
Sender: Codex
Recipient: Antigravity
Message Type: ASSIGNMENT
Timestamp: 2026-11-16T14:27:43.3605524+05:30
Related Message ID: EVALUATION-A4-PHASE-3-008
Current Task Status: ASSIGNED

# NERO Implementation Assignment

Task ID: A4-QLF-001
Task Title: 12-Step Release Qualification Engine
Milestone: A4 Phase 4, qualification and audit
Priority: High; execute first
Authorization ID: NERO-A4-GATE3-20261115-001

## Objective

Evaluate the approved twelve release checks deterministically and return a structured, fail-closed decision without persistence or fabricated observations.

## Background

Read `docs/architecture/NERO_A4_IMMUTABLE_RELEASE_REQUIREMENTS_ARCHITECTURE_AND_IMPLEMENTATION_PLAN.md` section 4, `PLAN-A4-PHASES-001`, Phase 3 acceptance, candidate/manifest/distribution/security contracts. The approved list is: (1) candidate schema/checksum; (2) catalog/branch; (3) origin commit and clean source; (4) remote artifact presence; (5) digest parity; (6) SBOM completeness; (7) provenance validity; (8) signature verification; (9) security gate; (10) diff coverage >=80%; (11) environment compatibility; (12) rollback readiness.

## Existing Files to Inspect

`platform_core/models/candidate_contract.py`, `platform_core/models/release_manifest_v2.py`, `platform_core/engine/distribution_dispatcher.py`, `platform_core/engine/supply_chain_aggregator.py`, `platform_core/catalog/applications.yaml`, and the A4 architecture/checklist. Inspect actual APIs before finalizing names.

## Files Allowed to Modify

`platform_core/engine/release_qualification.py` and `tests/unit/test_release_qualification.py` only, plus Antigravity's own acknowledgement/result messages.

## Files Prohibited from Modification

All other source/tests, application files, Docker/Jenkins/Terraform, catalog, release catalog, audit ledger, Codex messages/status, and protected keys.

## Implementation Requirements

Expose typed `QualificationInput`, `QualificationCheckResult`, `QualificationReport`, and `evaluate_release(input) -> report` (or equivalent clearly documented API). Input binds candidate ID/checksum, release ID/checksum, app ID, target environment, immutable component identities, observed origin/clean-tree proof, registry/object-storage receipts, supply-chain aggregation, scanner/security decision, diff coverage, environment constraints, and rollback evidence. Each observation must identify its source and subject; absent, stale, contradictory, or untrusted observations fail that check. Produce exactly twelve ordered results with stable IDs, PASS/FAIL, reason/evidence identifiers, and no success from a mere caller boolean. Report `QUALIFIED` only when all mandatory checks pass; otherwise `REJECTED`, with failure list. Do not mutate candidate or manifest, change `ReleaseQualification`, change FSM state, mint a release, or append audit records. Design the Step 9 input contract so QLF-003 can produce it without changing this file; describe its required finding-level evidence and trusted policy version. No external network or live service call in this task.

## Security Requirements

Validate checksum and cross-object identity before using evidence. Missing scanner data, unverified SBOM/provenance/signature, skipped tests, coverage below 80%, drift, missing rollback target, and fabricated origin/registry observations fail closed. Do not infer live verification from Phase 3 mocked tests.

## Test Requirements

Test all twelve positive/negative paths, missing evidence for each step, component identity/digest mismatch, boundary coverage 79.99/80.0, zero-skipped rule, order determinism, and input immutability. Run isolated suite and existing 12-suite regression.

## Acceptance Criteria

Exactly twelve ordered check results; no mandatory failure yields `QUALIFIED`; reasons identify missing/mismatched evidence; all tests pass and protected baselines stay unchanged.

## Infrastructure Restrictions

No authoritative ledger append, real AWS, live Docker/Jenkins/Terraform mutation, commits or pushes. Use temporary/mock data only.

## Expected Deliverables

Two allowed files, `ACK-TASK-A4-QLF-001.md`, and `RESULT-TASK-A4-QLF-001.md`.

## Completion Report Requirements

Document API, twelve checks, exact test commands/counts, evidence gaps, changed files, and audit/Terraform baselines. Report implementation completion, not acceptance.

## Stop Conditions

Stop and ask through Markdown for architecture/scope ambiguity or need for prohibited edits. Publish result before starting QLF-002. Do not begin Phase 5.
