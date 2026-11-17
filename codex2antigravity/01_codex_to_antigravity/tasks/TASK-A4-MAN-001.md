Message ID: TASK-A4-MAN-001
Task ID: A4-MAN-001
Sender: Codex
Recipient: Antigravity
Message Type: ASSIGNMENT
Timestamp: 2026-11-15T00:00:13.7886524+05:30
Related Message ID: None
Current Task Status: ASSIGNED

# NERO Implementation Assignment

Task ID: A4-MAN-001
Task Title: Universal Release Manifest v2 Schema
Milestone: A4 Milestone 1, Candidate Ingestion and Release Manifest Architecture
Priority: High; prerequisite for A4-MAN-002
Authorization ID: NERO-A4-MAN-001-TASK-AUTH-20261114-001 (Platform Owner directive in this session; limited to this task)

## Objective

Implement and test an in-memory Pydantic v2 `ReleaseManifestV2` contract for multi-component immutable releases. Publish no artifacts or audit events. Programme Gate 3 remains pending; this is a task-specific authorization only.

## Background

Read the A4 manifest schema in `nero_devops_standard/docs/architecture/NERO_A4_IMMUTABLE_RELEASE_REQUIREMENTS_ARCHITECTURE_AND_IMPLEMENTATION_PLAN.md` and task entry in `NERO_A4_IMPLEMENTATION_READINESS_AND_KICKOFF_PLAN.md`. The accepted candidate model is `platform_core/models/candidate_contract.py`; its artifact types are `OCIImageArtifact`, `StaticArtifact`, and `WorkerArtifact`. Use `platform_core/models/canonical_json.py` (`canonicalize_jcs` and `compute_contract_checksum`) for deterministic bytes and SHA-256. The legacy reference is root `release-manifest.json`. The current canonical number formatter has a documented RFC 8785 float-boundary limitation; do not claim complete RFC 8785 conformance or alter that shared module under this task.

## Existing Files to Inspect

- `platform_core/models/candidate_contract.py`, `canonical_json.py`, and `__init__.py`
- `platform_core/engine/candidate_ingest.py` for accepted candidate inputs, read only
- `release-manifest.json` and the two A4 architecture documents above, read only
- `tests/unit/test_candidate_contract.py` and `tests/unit/test_candidate_ingest.py`, read only

## Files Allowed to Modify

- `platform_core/models/release_manifest_v2.py` (new model and pure converters)
- `tests/unit/test_release_manifest_v2.py` (new isolated unit suite)
- `platform_core/models/__init__.py` (exports only; preserve existing exports)
- Antigravity's own new acknowledgement, question/blocker if needed, and result messages under `nero_devops_standard/codex2antigravity/02_antigravity_to_codex/`

## Files Prohibited from Modification

All other files, including `backend/`, `frontend/`, Dockerfiles, Jenkins pipelines, Terraform and state, `platform_core/audit/audit_log.jsonl`, `canonical_json.py`, candidate contract and ingestion modules/tests, the root legacy manifest, Codex communication files, and status/register files. Do not reformat unrelated code.

## Implementation Requirements

1. Define strict Pydantic v2 models (`extra='forbid'`) with an exported `ReleaseManifestV2`, `ReleaseComponent` discriminated by component type, `ReleaseProvenance`, `ReleaseSupplyChain`, `ReleaseQualification`, and promotion-history entries. Preserve component names as stable map keys, require at least one component, reject duplicate or mismatched names, and use explicit schema identity (`platform.nero/v2`, `ReleaseManifest`, or equivalent fields documented in the model). Do not conflate qualification state with later release FSM transitions.
2. Support container, static tarball, and background worker components. A container carries registry/repository or image reference plus a pinned `sha256:` digest of exactly 64 lowercase hex characters; immutable identity must use the digest, never a mutable tag alone. A static artifact carries a storage path/key, positive byte size, and `sha256:` byte checksum. A worker carries a pinned container image and optional queue binding. Reject empty or unsafe artifact paths, negative sizes, malformed digests, and ambiguous image references. Reuse accepted candidate constraints where practical.
3. Provenance records source repository, valid 40- or 64-character lowercase Git commit SHA, branch, trusted builder identity, CI execution/run ID, and valid `cand-...` contract ID. Supply-chain fields allow explicit *absent* SBOM (Syft/CycloneDX), in-toto provenance, and Cosign signature references until later tasks produce them. Never synthesize claims that scanning, signing, or registry verification occurred.
4. Qualification starts `UNQUALIFIED`; allow the defined later states `DEVELOP_QUALIFIED`, `QA_QUALIFIED`, and `PRODUCTION_READY` as data values. Initial promotion history is empty. Promotion entries must have environment, actor, UTC timestamp, status, and digest-verification result; reject malformed values. This task models states and history only; no promotion or qualification engine.
5. Require a semver release version/tag consistent with the candidate contract, a stable release identifier, and a 64-character lowercase hexadecimal `payload_checksum`. Compute it as SHA-256 over canonical JSON UTF-8 bytes of the complete manifest payload excluding only the top-level `payload_checksum`. Reuse `canonicalize_jcs`/`compute_contract_checksum`; do not introduce a second canonicalizer. Provide documented `compute_payload_checksum()` and `verify_checksum()` methods plus a controlled factory/sealing path. Parsing a purportedly sealed manifest with a missing or mismatched checksum must fail closed; changing any modeled field, including metadata, must invalidate verification. Keep the stored model immutable or validate assignment to prevent unverified silent mutation. Avoid floats in the checksummed schema where existing canonicalization is known to diverge from full RFC 8785.
6. `from_candidate_contract(contract: CandidateReleaseContract, release_tag: str, ...)` must verify the candidate's checksum and the provided semver tag, carry over *actual* artifact digests, sizes, source and execution provenance, worker queue binding, and candidate ID, then create a sealed initial manifest with no fabricated SBOM/signature/qualification claims. Reject missing required source evidence. Factory behavior must be deterministic for identical explicit inputs; require explicit timestamp/identity inputs if otherwise nondeterministic.
7. `from_legacy_manifest(legacy_dict: dict, ...)` converts a sufficiently complete Phase 3 structure into the same validated v2 model. Map `application`, `source`, `build`, `components`, `sbom` and `provenance` references where evidenced; treat unsigned references as references, not verified attestations. Accept optional explicit trusted migration inputs if needed, but never silently invent a Git SHA, CI run ID, tarball size, or artifact checksum. Reject conflicts between `components` and `raw_components`. The checked-in root legacy sample contains `source.commit_sha: 'unknown'` and no frontend size, so it must raise a clear migration validation error unless the caller supplies verified missing values. Include a successful complete legacy fixture and a fail-closed test for the checked-in sample.
8. No filesystem, network, registry, cloud, audit-ledger, or subprocess side effects in model construction or converters. `A4-MAN-002` owns persistence, catalog indexing, and production serializer integration.

## Security Requirements

Reject malformed identifiers, checksums, paths, timestamps, and OCI digests. Never accept a tag as a substitute for a digest, or treat placeholder supply-chain references as verified evidence. Maintain local-only execution. Exclude secrets from examples and tests. Model validation must fail closed on unknown fields and incomplete legacy provenance.

## Test Requirements

Write isolated tests for: valid single and multi-component manifests; worker queue; invalid OCI digests; missing/mismatched payload checksum; malformed semver/release tag; negative static size; invalid Git SHA; dictionary insertion-order checksum stability; tampering with each component and a metadata field; valid and invalid candidate conversion; complete legacy conversion; rejection of the actual incomplete legacy sample; and no audit-ledger writes. Run `python -B -m unittest tests.unit.test_release_manifest_v2 -q` and `python -B -m unittest tests.unit.test_candidate_contract tests.unit.test_candidate_ingest tests.unit.test_release_manifest_v2 -q` from repository root. Use temporary data only; do not run tests that mutate authoritative infrastructure.

## Acceptance Criteria

- The public models validate all three artifact types and reject malformed or unsealed payloads.
- Canonical payload checksum is stable across equivalent dictionary insertion orders and fails verification after any field tampering.
- Candidate conversion preserves actual provenance and artifact integrity values and starts unqualified with no promotions or fabricated attestations.
- Complete legacy data converts; checked-in incomplete legacy data fails with a specific missing-evidence reason.
- Both test commands pass; existing 61 candidate tests continue to pass.
- Only allowed implementation files change; authoritative ledger and Terraform state remain at the pre-task baselines (84 records and matching SHA-256 `77072d885be691c71a30514be97666a7937deb0aa87ac6f52f5490733c1ddf83`; local state serial 23, 15 managed resources).

## Infrastructure Restrictions

No Docker/Jenkins/Terraform mutations, real AWS calls or credentials, cloud spend, global cleanup, audit-ledger rewrites, Git commits, or pushes. Do not overwrite pre-existing uncommitted work. Existing local service ports were closed during Codex's setup inspection; this task needs no live service.

## Expected Deliverables

The three allowed implementation files and immutable protocol messages. No deployment, manifest publication, or catalog mutation.

## Completion Report Requirements

Publish `02_antigravity_to_codex/results/RESULT-TASK-A4-MAN-001.md` with the protocol header, changed-file list, interface/field summary, exact test commands and results, negative-test evidence, candidate/legacy conversion evidence, ledger/Terraform baseline checks, deviations, unresolved risks, and Git status. Report `IMPLEMENTATION_COMPLETED`, not acceptance. Codex independently inspects the diff and code, reruns tests, and issues the acceptance verdict.

## Stop Conditions

First publish `02_antigravity_to_codex/acknowledgements/ACK-TASK-A4-MAN-001.md` with the protocol header and authorization ID. Stop affected work and publish a question for any ambiguity requiring architecture, security, scope, or authorization decisions. Stop on any need to edit prohibited files, missing trusted evidence, baseline drift, or unsafe external operation. Do not proceed to `A4-MAN-002`.
