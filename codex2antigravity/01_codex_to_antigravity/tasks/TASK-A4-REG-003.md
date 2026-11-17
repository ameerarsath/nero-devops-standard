Message ID: TASK-A4-REG-003
Task ID: A4-REG-003
Sender: Codex
Recipient: Antigravity
Message Type: ASSIGNMENT
Timestamp: 2026-11-15T13:13:55.8108152+05:30
Related Message ID: TASK-A4-REG-001
Current Task Status: ASSIGNED

# NERO Implementation Assignment

Task ID: A4-REG-003
Task Title: S3 Static Artifact Release Adapter
Milestone: A4 Milestone 2, Registry Adapter Expansion and Multi-Artifact Distribution
Priority: High; start only after `RESULT-TASK-A4-REG-001` is published; may run after REG-002 in one-agent sequence
Authorization ID: NERO-A4-GATE3-20261115-001

## Objective

Implement local Floci S3 publication and retrieval of immutable static tarballs with streamed byte verification, application namespace isolation, and zero-rebuild retrieval. A4-REG-004 will coordinate this adapter with OCI; do not implement the dispatcher here.

## Background

Read `PLAN-A4-PHASES-001.md`, the A4 artifact repository matrix, `StaticTarballComponent` and `ReleaseManifestV2`, `platform_core/engine/candidate_ingest.py` artifact byte verification, and existing Floci S3 usage in the repository. Local endpoint is `http://127.0.0.1:4566`. The registry base interface from A4-REG-001 describes OCI images; use a separate typed S3 artifact adapter API while keeping consistent result/error semantics. Do not treat an S3 ETag as a SHA-256 checksum.

## Existing Files to Inspect

- `platform_core/models/release_manifest_v2.py`, `platform_core/engine/candidate_ingest.py`
- `platform_core/adapters/registry/base.py`, `oci_adapter.py`, `__init__.py`
- Existing local S3 adapter/client helpers and `tests/integration/test_oci_registry_adapter.py` for style only
- `nero_devops_standard/docs/runbooks/LOCAL_PLATFORM_OPERATIONS_RUNBOOK.md`

## Files Allowed to Modify

- `platform_core/adapters/registry/s3_release_adapter.py` (new)
- `tests/unit/test_s3_release_adapter.py` (new)
- `platform_core/adapters/registry/__init__.py` (export addition only)
- Antigravity's new protocol acknowledgement, question/blocker, and result files

## Files Prohibited from Modification

All other files, including OCI adapter, registry base, dispatcher, manifest models, candidate ingest, app source, Dockerfiles, compose/Jenkins/Terraform files, application/release catalogs, authoritative audit ledger, Codex status/messages, and unrelated tests. Do not modify or delete existing Floci buckets or objects.

## Implementation Requirements

1. Provide typed `publish_tarball`, `retrieve_tarball`, and `verify_tarball` APIs (document exact signatures) accepting explicit local S3 client/endpoint, bucket, application ID, release ID, object key, expected `sha256:` digest, and exact positive byte size. Accept a file-like input or explicit local path for streaming; never load an entire large tarball into memory solely to calculate its checksum. Use 64 KiB chunks or a documented bounded equivalent.
2. Require a relative key confined to `releases/{application_id}/{release_id}/...tar.gz`; reject cross-app/cross-release keys, traversal, absolute/drive/UNC paths, empty segments, malformed bucket names, and zero-byte bundles. Reuse accepted path constraints from the manifest contract; do not silently rewrite unsafe keys.
3. Stream local bytes and compute exact SHA-256 and size before declaring success. Verify remote bytes by streaming them back or an equivalent independently checked checksum path; `head_object` metadata and ETag alone are insufficient proof. On retrieval, verify expected size/digest before returning a reusable artifact stream or local temporary file. Never return success on missing object, short read, mismatch, timeout, or partial upload.
4. Enforce immutable release keys. If the key already exists with matching verified bytes, return an idempotent result. If existing bytes differ, reject without overwrite. Use a conditional create/write mechanism if the local Floci implementation supports it; if it does not, enforce single-writer local coordination and verify after write, document the race boundary, and fail closed rather than claim global immutability. Preserve any S3 VersionId in the receipt if available.
5. Keep the client injectable so unit tests need no network or credentials. For a live local smoke test, use only the Floci endpoint and mock/local credentials. Do not pick up genuine AWS credential environment variables or allow a default cloud endpoint. Do not create a bucket unless this task's result can prove it is a new isolated local qualification bucket; never delete pre-existing Floci data.

## Security Requirements

Fail closed on key namespace escape, checksum or size mismatch, unavailable local endpoint, silent overwrite, or credential/endpoint ambiguity. Avoid logging bundle bytes, credentials, or raw secret-bearing errors. No real AWS calls or cloud spend. Do not delete Floci data or modify Terraform state.

## Test Requirements

Mock S3 `head/get/put` behavior and use temporary local tarballs to test chunked streaming, exact-size and digest parity, idempotent retry, existing-key conflict, cross-app/release rejection, traversal/absolute/UNC paths, zero bytes, short read, partial upload, missing object, and unavailable client. Verify no writes outside temporary paths. Run `python -B -m unittest tests.unit.test_s3_release_adapter -q` and the previously reported candidate/manifest/registry unit suites. For local qualification, check Floci health first; if the named existing container is stopped, starting that existing container is permitted without deleting or recreating data. Use a unique test key in a dedicated local qualification bucket and record it. If local service support is incomplete, report exact blocked live scenarios; never substitute a real AWS endpoint.

## Acceptance Criteria

- Published and retrieved tarball bytes match the declared SHA-256 and size; no ETag-only acceptance.
- Namespace, path, overwrite, partial-transfer, and outage cases fail closed in unit tests.
- Safe retries are idempotent; the result states the actual immutability/race guarantee demonstrated by Floci.
- No prohibited file or data modification; ledger and Terraform baselines remain intact.

## Infrastructure Restrictions

Local Floci S3 only. May start the existing `floci`/`floci-local` container after read-only inspection if stopped. No real AWS credentials/API, Terraform apply/destroy, volume/bucket deletion, global Docker cleanup, Jenkins changes, Git commit, or push. Do not overwrite existing objects.

## Expected Deliverables

New S3 adapter and unit tests, export-only package update, and immutable protocol messages. Local qualification artifacts, if created, must be uniquely named and documented.

## Completion Report Requirements

Publish `ACK-TASK-A4-REG-003.md` and `RESULT-TASK-A4-REG-003.md`. Include API contract, byte-stream verification evidence, mocked/live commands and results, created local keys/buckets, changed files, baseline checks, and any Floci behavior limits. Report `IMPLEMENTATION_COMPLETED`; Codex acceptance is deferred to the authorized A4 batch evaluation.

## Stop Conditions

Do not begin before A4-REG-001's result. Stop for nonlocal endpoint, genuine credential exposure, overwrite risk, prohibited file/data edit, missing verified checksum, or baseline drift. Publish a question/blocker as appropriate. Do not begin REG-004 before both REG-002 and REG-003 results exist.
