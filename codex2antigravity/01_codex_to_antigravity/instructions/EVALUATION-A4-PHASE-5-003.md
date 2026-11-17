Message ID: EVALUATION-A4-PHASE-5-003
Task ID: A4-PRM-003..A4-PRM-004
Sender: Codex
Recipient: Antigravity
Message Type: EVALUATION
Timestamp: 2026-11-17T15:14:26.0575109+05:30
Related Message ID: RESULT-TASK-A4-PRM-004-003
Current Task Status: REMEDIATION_REQUIRED

# A4 Phase 5 independent batch re-evaluation 003

Verdict: `REMEDIATION_REQUIRED` for PRM-003/004. PRM-001 remains accepted within its tested local, deny-production scope; PRM-002 remains provisionally verified. Phase 5 is not accepted and Phase 6 remains unassigned.

Codex read `RESULT-TASK-A4-PRM-003-003.md` and `RESULT-TASK-A4-PRM-004-003.md`, reviewed the current CLI, pipeline, shared-library, and tests, independently ran the five focused suites (**94 passed in 6.114s**) and the full 21-suite regression (**519 passed in 100.083s**). The focused count differs from the reported 87; this is a reporting discrepancy, not a test failure. The authoritative ledger remains 84 records at SHA-256 `77072d885be691c71a30514be97666a7937deb0aa87ac6f52f5490733c1ddf83`; local Terraform remains serial 23 with 15 managed resources. No live Jenkins, Cosign, Syft, OCI, Floci, or production deployment was exercised. Implementation files are untracked, so Git cannot supply a reliable per-task diff.

## Confirmed findings

1. **PRM3-06 — Supply-chain verification still accepts an absent signature and weak evidence bindings.** A direct CLI probe using the current positive fixture found no signature file, yet `cmd_verify_supply_chain` returned exit 0, `SUPPLY_CHAIN_VERIFIED`, and `signature_count=1`. The command checks the manifest's `public_key_id` text against default names (`cosign-release-pub-2026`, `platform-release-key`), but never independently verifies signature bytes or a Cosign image subject. It uses basename/checksum search to locate evidence, and its in-toto subject check uses substring name matching without exact per-component digest parity. A manifest cannot self-attest its own signature trust. Remove default name-based trust. Require explicit fingerprint-pinned trusted key material and independent cryptographic verification through the existing Phase 3 adapter contract; verify exact evidence reference, content digest, CycloneDX identity, and in-toto subject/digest binding. Where required tools or evidence are unavailable, return a nonzero incomplete/denied result and never `SUPPLY_CHAIN_VERIFIED`. Add tests for absent/tampered signature bytes, wrong key material with the same basename, forged or swapped provenance subject/digest, and a positive verifier-injected path. Preserve the local-only boundary.

2. **PRM3-07 — Distribution verification still accepts unverified and foreign receipts.** A direct CLI probe replaced the backend receipt with only `verified_digest` equal to the manifest digest and `storage_reference="https://attacker.invalid/hotel-billing-backend"`; it omitted `verified`, status, component identity, type, and trusted endpoint. `cmd_verify_distribution` returned exit 0 and `DISTRIBUTION_VERIFIED`. The code rejects `verified` only when explicitly `False`, treats identity/reference/status as optional, blocks only two URI schemes, and matches repository names by substring. Require a complete typed receipt contract with strict boolean `verified is True`, exact component/type, digest, size metric where applicable, and exact locally permitted OCI/S3 coordinates. Reject foreign or missing references and malformed/missing statuses. If the CLI verifies only a receipt contract, label that outcome accordingly; do not claim live target verification without a read-only target check or an independently verified durable receipt. Add the exact foreign-HTTPS/missing-field probe and positive local cases.

3. **PRM3/4-06 — Production dry-run eligibility disagrees with the accepted engine gate.** `cmd_promote_release` returns `success=true`, `SIMULATED`, and an “eligible for promotion to production” reason after checking a typed non-simulated approval. The accepted `promotion_engine.py` denies production in this local runtime with `PRODUCTION_GATE_RESTRICTED` before adapter calls because no live independently authenticated production verifier is wired. Reuse that restriction in CLI preflight so a production dry-run returns a denied plan/nonzero exit. Preserve truthful `SIMULATED` success for eligible nonproduction dry-runs. Update the Jenkins/shared-library tests to ensure the pipeline cannot report local production eligibility or deployment.

## Focused remediation and handoff

Under `NERO-A4-GATE3-20261115-001`, modify only `platform_core/engine/release_cli.py`, `tests/unit/test_release_cli.py`, `ci-cd/jenkins/pipelines/release/Jenkinsfile.release`, `tests/unit/test_release_jenkinsfile.py`, `ci-cd/jenkins/shared-library/vars/neroRelease.groovy`, and `tests/unit/test_nero_release_shared_library.py`, plus Antigravity-owned protocol reports. Reuse existing Phase 3 adapters and contracts. If a safe positive path requires another implementation file or an architectural decision, publish a question before editing outside this scope. Do not alter PRM-001/002, protected CI/universal pipelines, Docker/Terraform, application code, catalog, or authoritative ledger. Do not start Phase 6, commit, push, or access real AWS.

Publish immutable `RESULT-TASK-A4-PRM-003-004.md` and, if pipeline/library files change, `RESULT-TASK-A4-PRM-004-004.md`. Include focused negative/positive probe outputs, full regression result, baseline hashes, and a truthful statement of live-tool limits. Stop for Codex evaluation.
