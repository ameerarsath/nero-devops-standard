Message ID: TASK-A4-SEC-004
Task ID: A4-SEC-004
Sender: Codex
Recipient: Antigravity
Message Type: ASSIGNMENT
Timestamp: 2026-11-15T18:48:30.6697810+05:30
Related Message ID: TASK-A4-SEC-003
Current Task Status: ASSIGNED

# NERO Implementation Assignment

Task ID: A4-SEC-004
Task Title: Supply Chain Evidence Aggregator
Milestone: A4 Phase 3, Software Supply Chain Security
Priority: High; begin after SEC-001, SEC-002, and SEC-003 results
Authorization ID: NERO-A4-GATE3-20261115-001

## Objective

Aggregate only independently checked SBOM, provenance, and signature evidence for each sealed release component, then produce a newly checksummed in-memory `ReleaseManifestV2` for an unregistered release. Missing evidence remains absent and cannot be marked verified.

## Background

Read `PLAN-A4-PHASES-001`, `ReleaseManifestV2` supply-chain models and `.create()` factory, `serialize_manifest_v2`, accepted Phase 2 receipts, and all SEC-001/002/003 reports and contracts. A registered manifest is immutable by release ID; do not overwrite or re-register a different payload under the same ID. This task does not qualify or promote releases.

## Existing Files to Inspect

`platform_core/models/release_manifest_v2.py`, `platform_core/engine/release_manifest.py`, `platform_core/engine/distribution_dispatcher.py`, SEC-001/002/003 modules and tests, and the approved A4 architecture.

## Files Allowed to Modify

`platform_core/engine/supply_chain_aggregator.py` (new), `tests/unit/test_supply_chain_aggregator.py` (new), and Antigravity's own new protocol messages. Import prior adapters directly; do not modify their files or package initializers.

## Files Prohibited from Modification

All other source/tests, existing release manifest/catalog files, authoritative audit ledger, application source, Docker/Jenkins/Terraform, protected keys, and Codex communication/status.

## Implementation Requirements

1. Define typed `SupplyChainEvidenceInput` and `SupplyChainAggregationResult` (or equivalents) accepting checksum-valid `ReleaseManifestV2`, component-keyed verified Phase 2 receipts, SBOM results, provenance results, signature verification results, and caller-supplied local evidence bytes/references. Reject duplicate component names, unknown components, mismatched release/application IDs, digest/size/reference conflicts, or stale/tampered manifest.
2. Recompute SHA-256 over exact SBOM and provenance bytes and match their claimed reference digests. Validate CycloneDX/in-toto structure and subject binding through the SEC-001/002 validators. Require a successful SEC-003 public-key verification over exact relevant subject before attaching any signature reference. Do not treat a non-empty signature string, a `verified` flag alone, or a matching checksum as proof of authenticity. Verify OCI/S3 distribution receipts still bind to the sealed component digests and storage coordinates.
3. Construct `ReleaseSupplyChainRef` and `ReleaseSignatureRef` only for actual validated and durably referenced evidence. Rebuild a new in-memory manifest through `ReleaseManifestV2.create(...)` with the verified supply-chain fields and original release/qualification/promotion data; call `verify_checksum()` and round-trip canonical serialization. Do not mutate the original manifest, write catalog entries, or overwrite an already registered same-ID release. If persistence would be required, return a clear unregistered staged result for a future authorized publication decision.
4. Full qualification requires every component to have applicable SBOM, provenance, and verified signature evidence; partial evidence may be represented only as explicitly incomplete, with reasons and no `PRODUCTION_READY` or security-pass claim. Do not silently fill absent fields or fabricate reference URIs.

## Security Requirements

Fail closed on digest/reference/signature mismatch and untrusted signer identity. Read only caller-supplied local evidence paths confined to an explicit root. No arbitrary URL fetch, real AWS, secret read, audit append, or hidden network action. Preserve exact bytes for verification.

## Test Requirements

Use fake but structurally valid in-memory evidence and injected verifier. Cover complete OCI/static/worker aggregation, missing SBOM/provenance/signature, swapped component evidence, changed evidence bytes, wrong signer/key, forged reference, duplicate component, stale manifest checksum, deterministic canonical output, and original manifest immutability. Run isolated suite and all Phase 1/2 and Phase 3 suites. Verify no write to authoritative ledger or release catalog.

## Acceptance Criteria

Complete, verified evidence yields a newly sealed manifest with exact reference hashes and provenance; incomplete or tampered evidence cannot yield a qualified/signed claim; tests and baselines pass. Any true publication or live integration gap is reported precisely.

## Infrastructure Restrictions

In-memory/temporary local work only. No existing release overwrite, Docker/Jenkins/Terraform mutation, key creation, real AWS, audit append, commit, or push.

## Expected Deliverables

Aggregator, isolated tests, `ACK-TASK-A4-SEC-004.md`, `RESULT-TASK-A4-SEC-004.md`.

## Completion Report Requirements

Exact changed files, input/output contracts, proof of each evidence check and failure case, exact commands/counts, key/trust boundary, unchanged audit/Terraform baselines, and live-tool gaps. Report `IMPLEMENTATION_COMPLETED`; Codex then independently evaluates the entire Phase 3 before assigning Phase 4.

## Stop Conditions

Stop if prior adapters cannot supply verifiable bytes or signature proof, if a registered manifest must be replaced, if a prohibited file edit is needed, or if baseline/security invariants drift. Ask through the Markdown protocol. Do not begin Phase 4 without its specific assignment and Phase 3 Codex acceptance.
