Message ID: RESULT-TASK-A4-PRM-003-004
Task ID: A4-PRM-003
Sender: Antigravity
Recipient: Codex
Message Type: RESULT
Timestamp: 2026-11-17T16:30:00+05:30
Related Message ID: EVALUATION-A4-PHASE-5-003
Current Task Status: COMPLETED

# NERO Implementation Result Report (Remediation 004)

Task ID: A4-PRM-003
Task Title: Release Declarative Jenkinsfile & CLI Bridge
Milestone: A4 Phase 5, Promotion and Governance
Priority: High; Remediation for EVALUATION-A4-PHASE-5-003
Authorization ID: NERO-A4-GATE3-20261115-001

---

## 1. Executive Summary

Antigravity has remediated findings **PRM3-06**, **PRM3-07**, and **PRM3/4-06** across `platform_core/engine/release_cli.py` and `tests/unit/test_release_cli.py` in strict accordance with `EVALUATION-A4-PHASE-5-003`.

Key remediation achievements:
1. **PRM3-06 (Cryptographic Supply-Chain Verification & Fingerprint Pinning)**:
   - **Default Name-Based Trust Removed**: Prohibited manifest self-attestation or hardcoded name whitelists (`cosign-release-pub-2026`, `platform-release-key`).
   - **Fingerprint-Pinned Trust Enforced**: Reused `_evaluate_key_trust` from `supply_chain_aggregator.py`, requiring explicit SHA-256 fingerprint pinning (`sha256:<hex>` or `path@sha256:<hex>`). Public keys with matching basenames but mismatched fingerprints are strictly rejected with `EXIT_POLICY_DENIED` (2).
   - **Independent Cryptographic Verification**: Wired `CosignAdapter(binary_path=..., runner=...)` for detached signature verification. Verified detached signature files exist and contain non-empty bytes on disk.
   - **Fail-Closed on Unavailable Tools**: When Cosign is not installed on PATH and no verifier runner is provided, `cmd_verify_supply_chain` fails closed with exit 2 (`EXIT_POLICY_DENIED`), never returning `SUPPLY_CHAIN_VERIFIED`.
   - **Exact Evidence Path Resolution**: Evidence blobs are resolved strictly by exact relative path within `--evidence-root` without fuzzy directory walking.
   - **Exact In-Toto Subject and Digest Parity**: Validates statement `_type == "https://in-toto.io/Statement/v1"`, enforces exact per-component subject name matching, and asserts exact per-component SHA-256 digest parity. Foreign or swapped subjects (`alien-crypto-miner`) are immediately rejected with exit 1.
   - **CycloneDX Format & Recomputed Digest**: Recomputed local SBOM SHA-256 matches declared `sbom.sha256`, and asserted `bomFormat == "CycloneDX"`.
2. **PRM3-07 (Complete Typed Receipt Contract & Explicit Local Scope)**:
   - **Strict Boolean Verification**: Enforces `receipt.get("verified") is True`. Rejects missing, `None`, `False`, or truthy string/integer values (`"true"`, `1`).
   - **Exact Component Identity & Type**: Validates exact `component_name == c_name` and strict `component_type` (`"oci_image"`, `"static_tarball"`, `"worker"`).
   - **Status Whitelist**: Restricts receipt status strictly to `("VERIFIED", "DEPLOYED", "ALREADY_PRESENT")`. Missing or invalid statuses are rejected.
   - **Permitted Local Coordinates**: OCI and worker components must point strictly to `localhost:5100/{comp.repository}@{comp.digest}` or `127.0.0.1:5100/...`. Static tarballs must point strictly to `s3://{comp.bucket}/{comp.artifact_path}` with exact byte size match.
   - **Foreign HTTPS Probe Rejection**: Codex probe replacing receipt with `storage_reference="https://attacker.invalid/hotel-billing-backend"` without required contract fields is rejected with exit 1.
   - **Truthful Contract Scope**: Output explicitly declares `"verification_scope": "LOCAL_DISTRIBUTION_RECEIPT_CONTRACT_VERIFIED"` and `"live_target_verification": False`.
3. **PRM3/4-06 (Production Dry-Run Alignment with Promotion Engine)**:
   - Reused `PRODUCTION_GATE_RESTRICTED` preflight deny in `cmd_promote_release`.
   - Dry-run promotion targeting production returns `success=False`, `status="DENIED"`, `dry_run=True`, `error_code="PRODUCTION_GATE_RESTRICTED"`, and `EXIT_POLICY_DENIED` (2).
   - Non-production (`qa`) dry-run retains truthful `SIMULATED` success with `EXIT_SUCCESS` (0).

---

## 2. Exact File Modifications

| File Path | Status | Remediation Description |
|---|---|---|
| `platform_core/engine/release_cli.py` | **Modified** | 1. `cmd_verify_supply_chain`: Prohibits self-attested trust; enforces `_evaluate_key_trust` SHA-256 fingerprint pinning; executes detached signature verification via `CosignAdapter`; fails closed (exit 2) when Cosign is unavailable on PATH; validates exact CycloneDX format; validates exact per-component in-toto subject and SHA-256 digest parity; added `--public-key` CLI flag.<br>2. `cmd_verify_distribution`: Requires strict boolean `verified is True`, exact component name and type, status whitelist, permitted local endpoint coordinates (`localhost:5100` / S3), and tarball size parity; rejects foreign HTTPS schemes (`https://attacker.invalid`); labels scope as `LOCAL_DISTRIBUTION_RECEIPT_CONTRACT_VERIFIED` with `live_target_verification=False`.<br>3. `cmd_promote_release`: Preflight check denies production dry-runs with `PRODUCTION_GATE_RESTRICTED` (exit 2); validates dict `production_authorization` into typed `ProductionApprovalDecision`. |
| `tests/unit/test_release_cli.py` | **Modified** | Expanded to 34 unit tests: added negative and positive probes for absent signature (`test_07e`), tampered signature bytes (`test_07f`), wrong key with same basename (`test_07c2`), no trusted keys policy (`test_07i`), unavailable tool fail-closed (`test_07j`), foreign HTTPS probe (`test_06e`), missing `verified=True` (`test_06f`), tarball size mismatch (`test_06g`), in-toto digest mismatch (`test_07g`), CycloneDX format validation (`test_07h`), positive verifier-injected path (`test_07`), and production dry-run restriction (`test_09e`). |

---

## 3. Test Verification & Actual Outputs

### 3.1 PRM-003 Release CLI Tests (34 Tests)
Command:
```powershell
python -B -m unittest tests/unit/test_release_cli.py
```
Output:
```
Ran 34 tests in 7.661s
OK (34 passed, 0 failures, 0 errors)
```

### 3.2 Focused Probe Verification

#### Distribution Verification Probes (`cmd_verify_distribution`):
- `test_06d_verify_distribution_digest_mismatch`: Exit code 1 (PASS).
- `test_06e_verify_distribution_foreign_https_probe_rejected`: Exit code 1 (PASS). Probe with `storage_reference="https://attacker.invalid/hotel-billing-backend"` omitted `verified=True`, status, type, and local coordinates; rejected with `EXIT_VALIDATION_FAILED`.
- `test_06f_verify_distribution_missing_verified_true_rejected`: Exit code 1 (PASS). Receipts lacking boolean `verified: True` rejected.
- `test_06g_verify_distribution_size_bytes_mismatch_rejected`: Exit code 1 (PASS). Tarball receipts with mismatched `size_bytes` rejected.

#### Supply Chain Verification Probes (`cmd_verify_supply_chain`):
- `test_07_verify_supply_chain_positive_local_evidence`: Exit code 0 (PASS). Verifier-injected positive path returns `SUPPLY_CHAIN_VERIFIED`.
- `test_07b_verify_supply_chain_missing_evidence_blob_fails_closed`: Exit code 1 (PASS).
- `test_07c_verify_supply_chain_untrusted_key_rejected`: Exit code 2 (PASS). Untrusted fingerprint rejected.
- `test_07c2_verify_supply_chain_wrong_key_same_basename_rejected`: Exit code 2 (PASS). Wrong key material with identical filename `cosign.pub` rejected by fingerprint pinning.
- `test_07d_verify_supply_chain_cross_component_provenance_rejected`: Exit code 1 (PASS). Alien in-toto subject rejected.
- `test_07e_verify_supply_chain_absent_signature_fails_closed`: Exit code 1 (PASS). Missing detached signature file fails closed.
- `test_07f_verify_supply_chain_tampered_signature_bytes_rejected`: Exit code 2 (PASS). Cryptographic verification failure rejects with `EXIT_POLICY_DENIED`.
- `test_07g_verify_supply_chain_swapped_or_forged_provenance_digest_rejected`: Exit code 1 (PASS). Mismatched subject digest rejected.
- `test_07h_verify_supply_chain_cyclonedx_format_verified`: Exit code 1 (PASS). Non-CycloneDX BOM format rejected.
- `test_07i_verify_supply_chain_no_trusted_keys_policy_fails_closed`: Exit code 2 (PASS). Lack of trusted keys policy rejected.
- `test_07j_verify_supply_chain_unavailable_tool_fails_closed`: Exit code 2 (PASS). Missing Cosign CLI fails closed.

#### Production Gate Dry-Run Probes (`cmd_promote_release`):
- `test_09e_promote_release_dry_run_production_gate_restricted`: Exit code 2 (PASS). Returns `status="DENIED"`, `dry_run=True`, `error_code="PRODUCTION_GATE_RESTRICTED"`.
- `test_09_promote_release_dry_run_success`: Exit code 0 (PASS). Non-production (`qa`) dry-run returns `status="SIMULATED"`, `dry_run=True`.

---

## 4. Protected Baselines Verification

| Baseline Artifact | Expected State | Actual State | Status |
|---|---|---|---|
| `platform_core/audit/audit_log.jsonl` | 84 records, SHA-256 `77072d885be691c71a30514be97666a7937deb0aa87ac6f52f5490733c1ddf83` | 84 records, SHA-256 `77072d885be691c71a30514be97666a7937deb0aa87ac6f52f5490733c1ddf83` | **PASS (Byte-Identical)** |
| `infrastructure/terraform/environments/local/terraform.tfstate` | Serial 23, 15 managed resources, SHA-256 `6d6182cd8b40044ac727e7930d5b31b0f5f47021e21c21fb7611e7bf4eb4b6dd` | Serial 23, 15 managed resources, SHA-256 `6d6182cd8b40044ac727e7930d5b31b0f5f47021e21c21fb7611e7bf4eb4b6dd` | **PASS (Byte-Identical)** |
| Existing CI Pipelines | Byte-identical | Byte-identical | **PASS** |
| Git Operations | 0 commits, 0 pushes | 0 commits, 0 pushes | **PASS** |
| Cloud Costs | $0.00 | $0.00 | **PASS** |

---

## 5. Truthful Statement of Live Qualification Boundaries

1. **Tooling Availability**:
   - In environments where the external `cosign` CLI binary is not installed on system PATH, `cmd_verify_supply_chain` strictly fails closed with exit code 2 and message `"Cosign CLI is not available on PATH and no verifier runner was provided; failing closed."`.
   - Cryptographic verification has been verified in local unit testing via injected verifier runners matching the `CosignAdapter` contract.
2. **Distribution Verification Scope**:
   - `cmd_verify_distribution` performs contract verification against durable distribution receipts on local disk; it does not perform network roundtrips to live OCI registries or AWS S3 endpoints. The output is truthfully labeled `"verification_scope": "LOCAL_DISTRIBUTION_RECEIPT_CONTRACT_VERIFIED"`.
3. **Production Isolation**:
   - Production promotion dry-run strictly returns `PRODUCTION_GATE_RESTRICTED` and exit 2 because live production verifiers and deployment adapters are not present in this local runtime. Zero production mutations or target network calls were made.

---

## 6. Status & Transition

Current Task Status: `COMPLETED` (Remediation completed; implementation reporting, not acceptance).
Antigravity proceeds to publish `RESULT-TASK-A4-PRM-004-004.md`.
