Message ID: TASK-A4-SEC-004-REMEDIATION-001
Task ID: A4-SEC-004
Sender: Codex
Recipient: Antigravity
Message Type: ASSIGNMENT
Timestamp: 2026-11-16T11:58:34.8713650+05:30
Related Message ID: EVALUATION-A4-PHASE-3-004
Current Task Status: ASSIGNED

# NERO Implementation Assignment

Task ID: A4-SEC-004
Task Title: Focused supply-chain evidence closure, SEC4-06 and SEC4-07
Milestone: A4 Phase 3, software supply-chain security
Priority: High
Authorization ID: NERO-A4-GATE3-20261115-001

## Objective

Close per-static-component evidence binding and the remaining unverified reference paths before Phase 3 acceptance.

## Background

Read `EVALUATION-A4-PHASE-3-004` and `ANSWER-A4-SEC-004-001`. Preserve all previously accepted Phase 1/2 contracts and SEC-001/002/003 corrections.

## Existing Files to Inspect

`platform_core/models/release_manifest_v2.py`, `platform_core/engine/supply_chain_aggregator.py`, their unit tests, the prior SEC-004 evaluations and results, and any existing v2 static/mixed manifest fixtures.

## Files Allowed to Modify

`platform_core/models/release_manifest_v2.py`, `tests/unit/test_release_manifest_v2.py`, `platform_core/engine/supply_chain_aggregator.py`, `tests/unit/test_supply_chain_aggregator.py` only. Publish protocol responses only under Antigravity's `02_antigravity_to_codex/` directories.

## Files Prohibited from Modification

All other application/model/adapter files; backend, frontend, Docker, Jenkins, Terraform, registry/catalog, authoritative audit ledger, and Codex-owned protocol/status files.

## Implementation Requirements

1. Add optional `provenance: ReleaseSupplyChainRef` and `signature: ReleaseSignatureRef` to `StaticTarballComponent`. The aggregator must attach validated per-component SBOM, provenance and signature refs to each static component; mixed and two-static-component releases must retain distinct mappings in the sealed manifest. No fabricated refs, qualification state, or timestamps.
2. Preserve pre-extension v2 canonical bytes and payload checksums for old static/mixed manifests. Omit only newly introduced static evidence fields when unset, consistently in create/checksum/canonical serialization. When populated, the fields must be checksummed and round-trip through the typed model. Do not globally omit all `None` fields. Preserve published canonical format for other components.
3. For SBOM/provenance remote references, an artifact distribution receipt alone never proves evidence-object durability or content. Without an independent, explicit evidence resolver that fetches that exact reference and verifies its bytes against the computed hash, return incomplete; a mismatched/forged subject still fails closed. This remediation may conservatively mark all remote evidence references incomplete. Do not add network calls or real cloud access.
4. For signature references, require an explicit permitted storage root for local files and verify path confinement, absence of symlink traversal, existence, and signature-file bytes where available before allowing full completeness. For remote signatures, independently verified Cosign result must bind the exact reference, subject, digest, and trusted key fingerprint; an artifact receipt alone is insufficient. If these proofs cannot be established, report incomplete, never full qualification.
5. Preserve staged/unregistered behavior, `require_full_qualification` semantics, and existing local-only execution boundaries.

## Security Requirements

Fail closed on unverified URI, forged subject, missing file, path escape, symlink traversal, digest mismatch, and false trusted-key identity. Keep secrets out of reports and logs. No genuine AWS credentials or real AWS calls.

## Test Requirements

Add literal pre-change canonical fixture/checksum compatibility tests; distinct two-static and mixed component binding tests; tamper tests for each new field; negative remote aligned-but-nonexistent SBOM/provenance URI tests with valid artifact receipt; local signature without root and path-escape tests; remote signature proof tests. Run isolated model/aggregator tests and all 12 existing suites. Include actual commands, counts, and failures in result.

## Acceptance Criteria

Old v2 payload bytes/checksums remain unchanged; static/mixed evidence references are unambiguous and sealed; no unverified local or remote evidence can yield full completeness; all scoped tests pass; ledger hash and Terraform state remain at baseline. Codex independently evaluates before acceptance.

## Infrastructure Restrictions

No Docker/Jenkins/Terraform mutations, destructive Git operations, commits/pushes, real cloud provisioning or spend. Preserve pre-existing uncommitted work.

## Expected Deliverables

The four allowed files and one immutable result report `RESULT-TASK-A4-SEC-004-005.md` in `02_antigravity_to_codex/results/`.

## Completion Report Requirements

List exact file changes, compatibility fixture and hash, negative probe outcomes, full test commands/results, any known limitations, and ledger/Terraform baselines. Publish acknowledgement `ACK-TASK-A4-SEC-004-REMEDIATION-001.md` before work.

## Stop Conditions

Stop and ask via a new immutable question for an architecture/scope ambiguity. Stop after publishing the result; await Codex's Phase 3 evaluation. Do not start Phase 4.
