Message ID: TASK-A4-REG-002
Task ID: A4-REG-002
Sender: Codex
Recipient: Antigravity
Message Type: ASSIGNMENT
Timestamp: 2026-11-15T13:13:55.7319400+05:30
Related Message ID: TASK-A4-REG-001
Current Task Status: ASSIGNED

# NERO Implementation Assignment

Task ID: A4-REG-002
Task Title: Expanded OCI Distribution Adapter
Milestone: A4 Milestone 2, Registry Adapter Expansion and Multi-Artifact Distribution
Priority: High; start only after `RESULT-TASK-A4-REG-001` is published
Authorization ID: NERO-A4-GATE3-20261115-001

## Objective

Adapt the existing OCI registry adapter to the typed A4-REG-001 interface and enforce immutable digest identity, local tag conflict rejection, and remote manifest verification against the local registry. Preserve the legacy adapter API for existing callers.

## Background

Read `TASK-A4-REG-001`, its implementation result, `platform_core/adapters/registry/base.py`, existing `oci_adapter.py`, `BasePlatformAdapter`, the A4 artifact repository matrix, and the existing OCI integration tests. The current adapter's `validate_prerequisites()` may return true after connection failure, and `tag_and_push()` may return `sha256:unknown`; both are prohibited on an A4 success path. The registry is expected at `127.0.0.1:5100`. A4-REG-001 is a prerequisite report, not yet a Codex acceptance verdict under batch review.

## Existing Files to Inspect

- `platform_core/adapters/registry/base.py`, `oci_adapter.py`, `__init__.py`
- `platform_core/adapters/base.py`, `platform_core/engine/errors.py`
- `tests/unit/test_registry_base.py`, `tests/integration/test_oci_registry_adapter.py`
- `nero_devops_standard/docs/runbooks/LOCAL_PLATFORM_OPERATIONS_RUNBOOK.md`

## Files Allowed to Modify

- `platform_core/adapters/registry/oci_adapter.py`
- `tests/unit/test_oci_adapter.py` (new)
- `platform_core/adapters/registry/base.py` and `tests/unit/test_registry_base.py` only for a minimal backward-compatible contract correction proven necessary by integration; document exact changes in the result
- Antigravity's new protocol acknowledgement, question/blocker, and result files

## Files Prohibited from Modification

Other files, including Dockerfiles, compose files, Jenkins, Terraform, S3 adapter, dispatcher, manifests/models, application source, catalog, authoritative audit ledger, Codex communication/status, and unrelated tests. Do not change the existing OCI integration test file merely to force a pass.

## Implementation Requirements

1. Implement the four A4-REG-001 typed operations on `OCIRegistryAdapter` or a clearly documented compatible bridge. Preserve `tag_and_push`, `get_manifest_digest`, `pull_image`, `list_repositories`, and `execute` for existing callers, routing success through verified behavior where applicable. A legacy caller must never receive a successful push receipt containing an invalid digest.
2. Restrict this implementation to an explicitly configured local registry endpoint (`localhost:5100` or `127.0.0.1:5100`). Reject schemes, userinfo, path injection, and nonlocal hosts on the A4 path. Docker commands must use argument lists, no shell interpolation, bounded timeouts, and sanitized error output.
3. Before publishing a tag, query its current remote manifest. If it exists with the same digest, return a verified idempotent result. If it exists with different bytes/digest, reject without retagging or pushing. Serialize competing local operations for the same repository/tag; after any push, fetch the manifest again and verify its `Docker-Content-Digest` header against SHA-256 of the exact response bytes and the expected pinned digest. Do not claim global immutability against writers outside this adapter; report that boundary.
4. Accept OCI/Docker manifest media types supported by the local registry. Validate the 64-lowercase-hex `sha256:` digest. Missing headers, malformed JSON, empty payloads, unavailable registry, non-2xx responses, or digest mismatch fail closed. Never use `sha256:unknown` or an unverified `docker inspect` fallback as proof of publication. Address the historical `OCI-01` finding by verifying registry existence/content, not syntax alone.
5. `retrieve_manifest` and `verify_digest` must use content-addressed references or prove a requested tag resolves to the pinned digest. `apply_retention` may provide only dry-run/protected-digest behavior in this phase; no actual deletion is authorized here. Do not alter Go builder or Distroless Dockerfiles. Record exact tag/platform digest verification only if independently obtained from existing local images; otherwise leave it for the later authorized adoption gate.

## Security Requirements

Fail closed on mutable tag overwrite, registry outage, malformed digest, remote-content mismatch, and path/endpoint injection. Do not contact cloud registries or use genuine credentials. Preserve the existing registry data and volume. Do not pull unknown images from the internet to make tests pass.

## Test Requirements

Use mocked HTTP/Docker interactions for successful publish, idempotent same-digest retry, conflicting tag, missing digest header, wrong bytes, timeout, nonlocal endpoint, malformed digest, concurrent local calls, and legacy API compatibility. Run `python -B -m unittest tests.unit.test_registry_base tests.unit.test_oci_adapter -q` and the existing candidate/manifest suites. For local qualification, first check `/v2/` read-only. If the named existing registry container is stopped, starting that existing container is permitted; do not recreate or delete it or its volume. Run a live smoke test only with a disposable, unique test tag in an existing local repository and preserve all prior tags. If Docker/service is unavailable, report the live test as blocked with exact evidence; do not claim it passed.

## Acceptance Criteria

- Typed interface and legacy API agree on verified digest results; no success path returns an unverified digest.
- Same-digest retry is idempotent, different-digest tag collision is rejected, and remote manifest bytes/header/expected digest match before success.
- Mocked negative tests pass, existing regression tests continue passing, and local smoke evidence is either successful or explicitly blocked with cause.
- Only allowed files change; authoritative audit ledger and Terraform state retain their recorded baselines.

## Infrastructure Restrictions

Local registry only. May start the existing `floci-aws-ecr-registry` container if stopped, after inspecting its state. Do not create/delete containers or volumes, run global cleanup, modify compose/Terraform/Jenkins, use AWS, commit, or push. No destructive registry operation.

## Expected Deliverables

Adapter integration, unit tests, and immutable acknowledgement/result messages. Any local smoke tag is recorded in the result and never overwrites existing tags.

## Completion Report Requirements

Publish `ACK-TASK-A4-REG-002.md` before work and `RESULT-TASK-A4-REG-002.md` after work. Include public API compatibility, digest verification trace, mocked/live test commands and outcomes, local-service state, changed files, baseline checks, and unresolved external-writer race limits. Report `IMPLEMENTATION_COMPLETED`; acceptance waits for the authorized A4 batch evaluation.

## Stop Conditions

Do not begin before A4-REG-001's result. Stop on a required nonlocal registry, prohibited file edit, data-loss risk, inability to verify a digest, or baseline drift. Publish a question/blocker as appropriate. Do not start A4-REG-003 or REG-004 merely because this task completes; follow their specific assignment and dependencies.
