Message ID: TASK-A4-SEC-003
Task ID: A4-SEC-003
Sender: Codex
Recipient: Antigravity
Message Type: ASSIGNMENT
Timestamp: 2026-11-15T18:48:30.6627838+05:30
Related Message ID: TASK-A4-SEC-002
Current Task Status: ASSIGNED

# NERO Implementation Assignment

Task ID: A4-SEC-003
Task Title: Cosign Digital Signing Adapter
Milestone: A4 Phase 3, Software Supply Chain Security
Priority: High; begin after SEC-002 result
Authorization ID: NERO-A4-GATE3-20261115-001

## Objective

Provide local-key Cosign signing and independent verification for exact pinned image digests and canonical evidence blobs, with an operational key-management runbook. No signature may be reported verified before successful public-key verification.

## Background

Read `PLAN-A4-PHASES-001`, approved A4 Milestone 3 and owner key-custody conditions, SEC-001/002 results, accepted local OCI adapter, and manifest supply-chain references. The current host has no confirmed Cosign executable or NERO `SecretManager` API. Discover actual local tool/help before constructing CLI arguments. If absent, implement typed unavailable handling and subprocess-injected unit tests, and report live qualification as pending. Do not invent a Cosign signature or substitute an incompatible algorithm while calling it Cosign.

## Existing Files to Inspect

`platform_core/models/release_manifest_v2.py`, `platform_core/adapters/registry/oci_adapter.py`, `platform_core/adapters/security/__init__.py`, `docs/architecture/NERO_A4_IMPLEMENTATION_READINESS_AND_KICKOFF_PLAN.md`, and SEC-001/002 results.

## Files Allowed to Modify

`platform_core/adapters/security/cosign_adapter.py` (new), `tests/unit/test_cosign_adapter.py` (new), `docs/runbooks/COSIGN_KEY_MANAGEMENT_RUNBOOK.md` (new), and Antigravity's own new protocol messages. No private/public key file in the repository under this assignment.

## Files Prohibited from Modification

All other code/tests, existing manifests and catalogs, application source, Docker/Jenkins/Terraform, authoritative audit ledger, secret stores, actual protected keys, and Codex communication/status.

## Implementation Requirements

1. Define typed signing/verification requests and results. Distinguish `image_digest` (`localhost:5100/<repo>@sha256:<64hex>`) and `blob` (caller-supplied canonical bytes plus exact SHA-256). Verify local endpoint/digest syntax, subject binding, signature reference, key identifier/fingerprint, tool version, and verification outcome. A result with `verified=True` requires a completed Cosign verification using the specified public key against exactly the signed subject.
2. Use Cosign CLI through argument vectors, bounded timeouts, no shell, and injected runner for tests. Keep key path and passphrase outside repo-controlled locations. Require password-encrypted private keys and explicit passphrase provider (or an explicitly injected `COSIGN_PASSWORD` child-process environment); do not accept empty passphrase or print it, the child environment, private-key bytes, or command output containing secrets. Never create an unencrypted fallback key. Use local-only registry interaction; disable public transparency-log upload/keyless/OIDC as appropriate to the installed Cosign version and prove the CLI flags with actual local help/version if available.
3. Separate sign from verify. For blobs, bind detached signature to canonical bytes and hash; reject changed bytes/signature/public key. For images, use only immutable `@sha256:` references, never tags; reject nonlocal registry and digest mismatch. Do not claim an OCI signature is published until Cosign confirms publication and verification. A missing CLI returns a typed unavailable outcome without a verified signature. Do not add an ad hoc pure-Python verifier that purports to validate Cosign's format.
4. The runbook must state encrypted key generation, passphrase injection and SecretManager/provider boundary, POSIX and Windows access restrictions, offline backup and restore, 90-day rotation procedure, compromise revocation/deny policy, trusted public-key distribution, and local trust limitations (no KMS/HSM, Rekor, or enterprise OIDC). Explain that installation/version readiness and production key custody require separate operational evidence. Never include an actual key, passphrase, or live secret value.

## Security Requirements

No real AWS credentials or public registry, no key in Git, no plaintext private key, no secrets in process arguments/logs/test output. Tests use fake runner and temporary dummy paths; if local Cosign is available, use only a disposable key under OS temp and a non-production subject. Preserve all existing keys and artifacts.

## Test Requirements

Cover valid mocked sign-and-verify, forged signature, changed digest/bytes, wrong public key, absent/empty passphrase, missing CLI, timeout/nonzero exit, nonlocal/tag reference, and secret redaction. Verify no false-positive `verified=True`. Run isolated suite and combined Phase 1/2 plus SEC-001/002/003 suites. Report whether a real local Cosign smoke test ran, and exact reason if not.

## Acceptance Criteria

No unverifiable signing success; offline public-key verification binds signature to exact subject; no secret or private key enters repository, logs, or protocol messages; tests pass; runbook provides usable local key custody steps.

## Infrastructure Restrictions

No package installation, live protected-key creation/rotation, registry mutation of existing artifacts, Terraform, Docker cleanup, audit append, real AWS, commit, or push. A disposable local smoke test is allowed only when CLI and safe temporary fixture are available.

## Expected Deliverables

Adapter, unit tests, key-management runbook, `ACK-TASK-A4-SEC-003.md`, `RESULT-TASK-A4-SEC-003.md`.

## Completion Report Requirements

Exact changed files, CLI version/availability, supported operations, full test commands/counts, safe smoke evidence or blocker, public-key verification evidence, secret-handling proof, and unchanged audit/Terraform baselines. Report `IMPLEMENTATION_COMPLETED`, not acceptance.

## Stop Conditions

Stop for needed prohibited edit, missing key-management contract, inability to disable external egress, unsafe CLI behavior, secret exposure, baseline drift, or any need to touch a protected key. Ask through protocol. Do not begin SEC-004 until this result is published.
