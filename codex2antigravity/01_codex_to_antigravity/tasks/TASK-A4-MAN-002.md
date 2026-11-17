Message ID: TASK-A4-MAN-002
Task ID: A4-MAN-002
Sender: Codex
Recipient: Antigravity
Message Type: ASSIGNMENT
Timestamp: 2026-11-15T11:21:01.0651075+05:30
Related Message ID: DECISION-A4-GATE3-001
Current Task Status: ASSIGNED

# NERO Implementation Assignment

Task ID: A4-MAN-002
Task Title: Manifest Serializer and Catalog Registrar
Milestone: A4 Milestone 1, Candidate Ingestion and Release Manifest Architecture
Priority: High; dependency for registry, supply-chain, and qualification phases
Authorization ID: NERO-A4-GATE3-20261115-001

## Objective

Implement deterministic, crash-aware local persistence and catalog registration for an already validated `ReleaseManifestV2`. The model contract A4-MAN-001 is accepted; this task turns it into an immutable local release record without changing the legacy build/release path or authoritative application catalog.

## Background

Read `PLAN-A4-PHASES-001.md`, `DECISION-A4-GATE3-001.md`, `platform_core/models/release_manifest_v2.py`, `platform_core/models/canonical_json.py`, `platform_core/engine/release_manager.py`, and `platform_core/engine/catalog.py`. A4-MAN-001 supplies `to_canonical_json()`, `compute_payload_checksum()`, `verify_checksum()`, and `from_json()`. `release_manager.py` currently writes the Phase 3 root `release-manifest.json`; that code remains read-only. This task's catalog is a **release catalog under an explicit caller-provided storage root**, separate from `platform_core/catalog/applications.yaml`.

## Existing Files to Inspect

- `platform_core/models/release_manifest_v2.py`, `canonical_json.py`, `candidate_contract.py`
- `platform_core/engine/release_manager.py`, `catalog.py`, and `errors.py`
- `tests/unit/test_release_manifest_v2.py`, `tests/unit/test_candidate_ingest.py`
- The A4 manifest specification and Milestone 1 plan under `nero_devops_standard/docs/architecture/`

## Files Allowed to Modify

- `platform_core/engine/release_manifest.py` (new serializer/registrar module)
- `tests/unit/test_release_manifest.py` (new isolated unit tests)
- Antigravity's new acknowledgement, question/blocker if necessary, and result messages under `nero_devops_standard/codex2antigravity/02_antigravity_to_codex/`

## Files Prohibited from Modification

All other repository files, especially `platform_core/models/release_manifest_v2.py`, `canonical_json.py`, `candidate_contract.py`, `platform_core/engine/release_manager.py`, `platform_core/engine/catalog.py`, `platform_core/catalog/applications.yaml`, existing manifests, root `release-manifest.json`, `platform_core/audit/audit_log.jsonl`, application source, Dockerfiles, Jenkins, Terraform configuration/state, Codex messages, and status/register files. Do not reformat unrelated code.

## Implementation Requirements

1. Expose a small typed public API in `release_manifest.py`: `serialize_manifest_v2(manifest: ReleaseManifestV2) -> bytes`, `register_manifest(manifest: ReleaseManifestV2, storage_root: Path) -> RegistrationResult`, and `load_registered_manifest(application_id: str, release_id: str, storage_root: Path) -> ReleaseManifestV2` (equivalent clearly documented names are acceptable). Keep storage root explicit; no default to the live repository. Do not invoke builds, network services, the legacy release manager, or the authoritative application catalog.
2. Serialization must call the accepted model's checksum guard and return its canonical UTF-8 JSON bytes, including the embedded `payload_checksum`. Reparse emitted bytes with `ReleaseManifestV2.from_json` before publication. Equivalent models with different dictionary insertion order must produce byte-identical output. Tampered or incomplete manifests must fail before any filesystem write.
3. Use a caller-selected release storage layout such as `storage_root/manifests/{application_id}/{release_id}.json` and a single `storage_root/catalog.json`. Catalog entries must bind `(application_id, release_id)` to relative manifest path, `payload_checksum`, and creation metadata. Reject path traversal/symlink escapes and derive paths only from validated identifiers. Never interpret arbitrary catalog paths outside the root.
4. Treat release IDs as immutable: registration of identical bytes is idempotent and reports `ALREADY_REGISTERED`; the same ID with different bytes/checksum fails closed without replacing either record. Loading must verify catalog-to-manifest checksum, IDs, and model checksum, and reject missing, stale, tampered, or orphaned records.
5. Make publication concurrency-safe and crash-aware. Acquire a cross-platform advisory lock under `storage_root` for index decisions and updates. Stage complete bytes in temporary files within the destination filesystem, flush and close them, then atomically rename. Do not expose a catalog entry before its manifest is durable. If index publication fails after a manifest rename, leave no visible valid catalog entry for it; a retry must safely recover or quarantine its own orphan without deleting unrelated files. Never overwrite an existing different manifest or catalog entry. Document the precise commit point and recovery behavior in code comments/docstrings.
6. The catalog index must be deterministic and schema-versioned. Validate it before update, reject duplicate keys or malformed entries, and canonicalize its JSON bytes with the existing canonicalizer. Preserve unrelated valid entries. Do not import or modify the application catalog. This task does not publish to OCI/S3, sign, qualify, promote, or append audit events; later phases own those operations.

## Security Requirements

Fail closed on checksum mismatch, malformed IDs, unsafe paths, duplicate index keys, symlink escape, and conflicting registration. Keep all writes under the explicitly passed storage root. Avoid logging secrets, manifest payloads, or untrusted path contents. Tests must not touch the authoritative audit ledger or Terraform state. Do not claim full general RFC 8785 float conformance; the v2 manifest schema avoids floats.

## Test Requirements

Use `tempfile.TemporaryDirectory()` for every persistence test. Cover canonical byte stability, valid registration/load, idempotent retry, same-ID conflict, tampered manifest and catalog rejection, missing manifest, malformed/duplicate index data, unsafe identifiers/path escapes, staged write and rename failure injection, recovery of own orphan, and two concurrent registrations. Assert zero writes outside the temporary root and unchanged authoritative ledger hash. Run `python -B -m unittest tests.unit.test_release_manifest -q` and combined `python -B -m unittest tests.unit.test_candidate_contract tests.unit.test_candidate_ingest tests.unit.test_release_manifest_v2 tests.unit.test_release_manifest -q` from repository root. Avoid live service dependencies.

## Acceptance Criteria

- API publishes and reloads a valid v2 manifest with byte-identical canonical serialization and exact checksum parity.
- A catalog entry is never visible for an incomplete, absent, conflicting, or invalid manifest; retries and concurrent attempts are deterministic and fail closed.
- Existing unrelated release records and all prohibited repository files remain untouched.
- New tests and the existing 88 candidate/manifest tests pass; temporary storage contains all test writes.
- Audit ledger and Terraform state retain the pre-task baseline: 84 records, ledger SHA-256 `77072d885be691c71a30514be97666a7937deb0aa87ac6f52f5490733c1ddf83`, local state serial 23 with 15 managed resources.

## Infrastructure Restrictions

Local filesystem tests only. No Docker/Jenkins/Floci changes, real AWS calls or credentials, cloud spend, Terraform apply/destroy, audit-ledger rewrite, Git commit, or push. Do not remove or overwrite existing uncommitted work. If a baseline changes unexpectedly, stop and report it.

## Expected Deliverables

The new serializer/registrar module, isolated unit suite, and protocol messages. Do not write production manifest/catalog data into the repository as part of implementation or tests.

## Completion Report Requirements

First publish `02_antigravity_to_codex/acknowledgements/ACK-TASK-A4-MAN-002.md`. On completion publish `02_antigravity_to_codex/results/RESULT-TASK-A4-MAN-002.md` with changed files, API contract, exact commands/results, failure-injection and concurrency evidence, storage-root isolation, ledger/Terraform baselines, deviations, and Git status. Report `IMPLEMENTATION_COMPLETED`; do not claim acceptance. Under the owner's approved batch cadence, Codex will defer routine independent acceptance evaluation until the authorized A4 batch completes, while continuing to manage assignments, blockers, and status.

## Stop Conditions

Stop and publish a question for architecture/security ambiguity or any need to modify prohibited files. Stop on checksum or baseline drift, unsafe paths, suspected data loss, or required destructive action. Do not expand into A4-REG-001 or other tasks without a specific published assignment. Never commit or push.
