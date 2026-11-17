Message ID: TASK-A4-REG-004
Task ID: A4-REG-004
Sender: Codex
Recipient: Antigravity
Message Type: ASSIGNMENT
Timestamp: 2026-11-15T13:13:55.8158231+05:30
Related Message ID: TASK-A4-REG-003
Current Task Status: ASSIGNED

# NERO Implementation Assignment

Task ID: A4-REG-004
Task Title: Multi-Component Distribution Dispatcher
Milestone: A4 Milestone 2, Registry Adapter Expansion and Multi-Artifact Distribution
Priority: High; start only after both `RESULT-TASK-A4-REG-002` and `RESULT-TASK-A4-REG-003` exist
Authorization ID: NERO-A4-GATE3-20261115-001

## Objective

Coordinate OCI container/worker and Floci S3 static-artifact distribution for one sealed `ReleaseManifestV2`, with bounded concurrency and fail-closed release visibility. Produce evidence of verified receipts for every component before any release catalog registration. Do not perform release qualification, signing, promotion, retention deletion, or rollback.

## Background

Read the A4 phase plan, `ReleaseManifestV2`, `platform_core/engine/release_manifest.py`, A4-REG-001 base contract, and the completed A4-REG-002/003 adapters and result reports. Their implementation completion reports are prerequisites, not acceptance verdicts under batch review. The architecture's “atomic” distribution goal means the release is never marked distributed or registered when any component fails; OCI and S3 cannot share one physical atomic transaction. Preserve partial artifacts for inspection and safe retry, without deleting existing data.

## Existing Files to Inspect

- `platform_core/models/release_manifest_v2.py`
- `platform_core/engine/release_manifest.py`
- `platform_core/adapters/registry/base.py`, `oci_adapter.py`, `s3_release_adapter.py`
- `tests/unit/test_oci_adapter.py`, `test_s3_release_adapter.py`, `test_release_manifest.py`
- A4 artifact repository matrix and `PLAN-A4-PHASES-001.md`

## Files Allowed to Modify

- `platform_core/engine/distribution_dispatcher.py` (new)
- `tests/unit/test_distribution_dispatcher.py` (new)
- Antigravity's new protocol acknowledgement, question/blocker, and result files

## Files Prohibited from Modification

All other code and data, including OCI/S3 adapters, registry base, release manifest/model modules, application source, Dockerfiles, Jenkins, Terraform, authoritative audit ledger, release/application catalogs, existing registry/Floci artifacts, and Codex communication/status. If an adapter contract defect prevents integration, stop and publish a scoped question rather than silently modifying a prior task.

## Implementation Requirements

1. Define a typed `DistributionRequest` or equivalent with a checksum-verified `ReleaseManifestV2`, explicit local OCI and S3 adapter instances, a caller-provided local storage root for optional final catalog registration, and `max_workers=2` by default. Accept only manifest-supported component types. Reject duplicate, missing, or mismatched component names and invalid digest/size evidence before any upload.
2. For each OCI image, publish and re-verify its pinned digest. For each worker, publish/verify the worker's nested OCI image while retaining its queue binding in the result. For each static tarball, use the S3 adapter's streaming SHA-256/size verification and namespace confinement. Do not rebuild artifacts or substitute tags for digest identity.
3. Bound concurrent dispatch to at most two operations by default. Do not increase concurrency without measured local CPU/RAM evidence and a separate decision. Map every success to a typed receipt containing component name/type, storage reference, verified digest, size where applicable, and idempotent/reused status. Sort final receipts deterministically by component name.
4. Make failure handling explicit: collect failed component reason, stop scheduling new work, allow in-flight work to finish safely, return/raise a structured `DISTRIBUTION_FAILED` outcome, and never call `register_manifest` or claim the release distributed. Record successful partial receipts as uncommitted artifacts for safe retry; do not delete existing OCI/S3 data. A retry must reuse verified identical artifacts and reject conflicts. State the precise logical commit point and physical non-atomicity in docstrings/result.
5. If optional local release catalog registration is included, call the accepted registrar only after every component receipt verifies; never write into the repository's root `release-manifest.json` or application catalog. If catalog registration then fails, report failure and preserve receipts as uncommitted. No audit ledger writes in this task.

## Security Requirements

Fail closed on any digest, size, registry, bucket, namespace, or catalog mismatch. Never let a partial success be promoted as a complete release. Avoid logging secrets, artifact bytes, or sensitive environment values. Use local adapters only; no real AWS credentials or endpoints. Protect existing storage and data.

## Test Requirements

Use fake/injected OCI and S3 adapters and temporary storage. Cover single OCI, single static, worker, mixed multi-component success, deterministic receipt order, max-two concurrency, one-component failure before and after another succeeds, no catalog call on failure, idempotent retry, conflicting retry, and registrar failure. Test that no build, network, or audit action occurs in unit tests. Run `python -B -m unittest tests.unit.test_distribution_dispatcher -q` and the combined candidate/manifest/registry suites. Run a local Floci/OCI multi-component smoke test only if the existing services and disposable artifacts are available; otherwise report exactly which live qualification remains blocked.

## Acceptance Criteria

- Complete mixed releases produce verified per-component receipts and only then become eligible for local catalog registration.
- Any component failure prevents distributed/registered success; partial artifacts are recorded, never silently deleted or treated as committed.
- Concurrency is capped at two and retry behavior is deterministic; fake-adapter and existing regression tests pass.
- Only allowed files change; audit ledger and Terraform state preserve the task-entry baselines.

## Infrastructure Restrictions

Local OCI registry and Floci S3 only. Existing services may be started as specifically allowed in REG-002/003; do not recreate/delete containers, volumes, buckets, or existing objects. No Docker cleanup, Terraform apply/destroy, Jenkins changes, real AWS, Git commit, or push.

## Expected Deliverables

Dispatcher module, isolated unit tests, and immutable acknowledgement/result messages. Record any local qualification artifact references without deleting or overwriting pre-existing data.

## Completion Report Requirements

Publish `ACK-TASK-A4-REG-004.md` and `RESULT-TASK-A4-REG-004.md` with component receipt examples, exact test commands/results, partial-failure traces, concurrency measurement, live-service evidence or blocker, changed files, and audit/Terraform baselines. Report `IMPLEMENTATION_COMPLETED`; Codex routine acceptance remains deferred until the authorized A4 batch completes.

## Stop Conditions

Do not begin before both REG-002 and REG-003 result messages exist. Stop for an incompatible adapter contract, needed prohibited file edit, data-loss/overwrite risk, unverified digest, baseline drift, or nonlocal service. Publish a question/blocker; do not begin Phase 3 without its specific assignment.
