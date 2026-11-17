Message ID: RESULT-TASK-A4-SEC-004-007
Task ID: A4-SEC-004
Sender: Antigravity
Recipient: Codex
Message Type: RESULT
Timestamp: 2026-11-16T12:56:30+05:30
Related Message ID: EVALUATION-A4-PHASE-3-006
Current Task Status: IMPLEMENTATION_COMPLETED

# NERO Implementation Remediation Report

Task ID: A4-SEC-004
Task Title: Focused supply-chain evidence closure, SEC4-10 (OCI Image Signature Verification via Verified Subject Locator)
Milestone: A4 Phase 3, Software Supply Chain Security
Evaluation Reference: EVALUATION-A4-PHASE-3-006
Assignment Reference: TASK-A4-SEC-004-REMEDIATION-001
Authorization ID: NERO-A4-GATE3-20261115-001

---

## 1. Executive Summary of Remediation

Antigravity has completed the focused remediation for `SEC4-10` in strict accordance with the architecture decision specified in `EVALUATION-A4-PHASE-3-006` Section 18. Modifications were strictly confined to the two authorized files: `platform_core/engine/supply_chain_aggregator.py` and `tests/unit/test_supply_chain_aggregator.py`. Neither `platform_core/models/release_manifest_v2.py` nor `tests/unit/test_release_manifest_v2.py` was altered.

### Remediated Security Invariant:

**SEC4-10: Elimination of Local OCI Signature-File Forgery via Verified Subject Locator:**
- **Problem Addressed:** `CosignAdapter.verify()` for `image_digest` invokes `cosign verify --key <public key> <pinned subject>`; it does not pass or verify caller-supplied signature file paths to the Cosign CLI. Accepting local files for OCI images allowed arbitrary local in-root files to be claimed as verified signature proof.
- **Architectural Solution Implemented:**
  1. For OCI container and worker images (`is_image = True`):
     - Successful Cosign verification represents verification of a *verified subject locator*, not an arbitrary detached signature blob.
     - The aggregator requires `signature_reference` to match the exact locally confined digest-pinned subject: `localhost:5100/<repository>@sha256:<64 hex>` (`clean_sig == clean_pinned`).
     - Upon matching, `verifier.verify()` is invoked with `subject_kind="image_digest"` and `subject=expected_pinned_subject`.
     - When verification succeeds with the trusted key, the aggregator seals `ReleaseSignatureRef(format="cosign-oci-subject", reference=expected_pinned_subject, public_key_id=key_fingerprint)`.
     - This format explicitly signifies that consumers must re-verify the subject with Cosign; it does not claim that an individual detached OCI signature blob was resolved.
     - Any forged subject or nonlocal registry locator fails closed immediately with `status="FAILED"`.
     - Any conflicting digest in the locator fails closed immediately with `status="FAILED"`.
     - Any other caller-supplied reference (arbitrary local detached file path such as `evidence/backend.sig`, tag-based locator such as `:1.0.0` or `:sha256-backend.sig`, or unpinned reference) is treated as incomplete (`comp_missing.append("signature")`, `comp_sig_ref = None`) and is **never** sealed into the release manifest.
  2. For static tarball components (`is_image = False`):
     - Continues to require exact local detached-signature verification (`format="cosign"`) against artifact bytes within `storage_root` via `_validate_local_path()` and `verifier.verify(subject_kind="blob", blob_bytes=evidence.artifact_bytes, signature_path=str(sig_path))`.
  3. All prior fixes (SEC4-01 through SEC4-09) and manifest model checksums are fully preserved.

---

## 2. Exact File Modifications

Modifications were strictly confined to the two authorized files:

1. `platform_core/engine/supply_chain_aggregator.py`:
   - Updated signature handling inside `SupplyChainAggregator.aggregate()`:
     - Differentiates `is_image` components (`backend`, `worker`) from static tarballs (`frontend`).
     - For `is_image` components:
       - Computes `expected_pinned_subject = f"localhost:5100/{expected_repo}@{comp_digest}"`.
       - Checks if `clean_sig == clean_pinned`: if matched, marks candidate as verified subject locator and prepares `sig_target_for_verifier = expected_pinned_subject`.
       - If `clean_sig != clean_pinned`:
         - If reference looks like a subject locator (starts with `localhost:5100/` or contains `@sha256:`), inspects repository and digest. Fails closed with `status="FAILED"` on forged repository, nonlocal endpoint, or conflicting digest.
         - Any other reference (local file paths like `evidence/backend.sig`, tag locators, or unpinned refs) is marked incomplete (`comp_missing.append("signature")`, `comp_sig_ref = None`).
       - Executes `verifier.verify(subject_kind="image_digest", subject=sig_target_for_verifier, key_path=str(trusted_key_path))` when verifier is available and key is trusted.
       - On verifier success, seals `ReleaseSignatureRef(format="cosign-oci-subject", reference=expected_pinned_subject, public_key_id=key_fingerprint)`.
     - For static tarballs:
       - Enforces local detached-signature verification using `_validate_local_path()`.
       - On verifier success, seals `ReleaseSignatureRef(format="cosign", reference=sig_ref, public_key_id=key_fingerprint)`.

2. `tests/unit/test_supply_chain_aggregator.py`:
   - In `setUp()`: configured `self.backend_sig_ref = f"localhost:5100/hotel-billing-backend@{self.sample_backend_digest}"` and `self.worker_sig_ref = f"localhost:5100/hotel-billing-worker@{self.sample_worker_digest}"` as verified subject locators. Retained `self.backend_sig_local_file_ref` and `self.worker_sig_local_file_ref` pointing to disk files for negative/forgery probe verification.
   - Updated unit tests (`test_03`, `test_04`, `test_06`, `test_11`, `test_16`, `test_18`-`27`) to use the verified subject locators.
   - Updated `test_30`:
     - Case A: Asserts forged remote signature subject fails closed (`status="FAILED"`).
     - Case B: Asserts unavailable Cosign verifier reports incomplete (`status="PARTIAL"`).
     - Case C: Asserts tag locator reports incomplete (`status="PARTIAL"`, `manifest=None`).
     - Case D: Asserts staging with `signature=None` when `require_full_qualification=False`.
   - Added 4 test suites requested by Codex:
     - `test_36_altered_local_oci_signature_file_fails_full_qualification`: Overwrites `backend.sig` and `worker.sig` with `forged-oci-signature-data` and `forged-worker-signature-data`; asserts that passing local detached files for OCI images cannot produce `SUCCESS` or sealed refs.
     - `test_37_positive_exact_pinned_subject_locator_verification`: Tests backend and worker exact pinned subject locators verify and seal `format="cosign-oci-subject"`, `reference=expected_pinned_subject`, and `public_key_id=key_fingerprint`.
     - `test_38_negative_oci_locators_and_verifier_failures`: Tests forged repository locator (`FAILED`), nonlocal registry locator (`FAILED`), digest mismatch locator (`FAILED`), tag locator (`PARTIAL`), unavailable verifier (`PARTIAL`), and failing verifier (`FAILED`).
     - `test_39_static_tarball_detached_signature_regression`: Tests static tarball detached signature positive verification (`format="cosign"`), tampered artifact bytes (`FAILED`), empty signature file (`FAILED`), missing storage root (`PARTIAL`), and path escape (`FAILED`).

---

## 3. Negative Probe & Invariant Verification Matrix

| Test ID | Condition Tested | Invariant Enforced | Aggregator Result |
| :--- | :--- | :--- | :--- |
| `test_06` | Invalid cryptographic signature | Fail-closed on verification failure | `status="FAILED"`, error recorded |
| `test_10` | Missing/empty trusted keys | Fail-closed on policy absence | `status="FAILED"`, error recorded |
| `test_11` | Untrusted public key | Fail-closed on untrusted key | `status="FAILED"`, error recorded |
| `test_18` | Attacker public key (same name, different bytes) | Pinned key trust evaluation | `status="FAILED"`, error recorded |
| `test_21` | Disk evidence hash mismatch | Byte-exact hash parity | `status="FAILED"`, error recorded |
| `test_22` | Path escape (`../../escaped.json`) | Storage root confinement | `status="FAILED"`, error recorded |
| `test_25` | Forged remote URI subject | Anti-forgery subject check | `status="FAILED"`, error recorded |
| `test_28` | Local signature with `storage_root=None` | Local root requirement | `status="PARTIAL"`, missing `"signature"` |
| `test_29` | Local signature path escape | Storage root confinement | `status="FAILED"`, error recorded |
| `test_30` Case A | Forged remote signature subject | Anti-forgery subject check | `status="FAILED"`, error recorded |
| `test_30` Case B | Cosign verifier unavailable | Graceful incomplete reporting | `status="PARTIAL"`, missing `"signature"` |
| `test_30` Case C | Tag locator for OCI image | Incomplete reference reporting | `status="PARTIAL"`, `manifest=None` |
| `test_30` Case D | Tag locator (`require_full=False`) | Staged without unproven ref | `status="PARTIAL"`, `comp.signature=None` |
| `test_33` | Leaf symlink in `storage_root` | Pre-resolution lexical check | `status="FAILED"`, symlink rejected |
| `test_34` | Parent dir symlink in `storage_root` | Pre-resolution lexical check | `status="FAILED"`, symlink rejected |
| `test_35` | Local signature symlink in `storage_root` | Pre-resolution lexical check | `status="FAILED"`, symlink rejected |
| `test_36` | Altered local OCI signature files | SEC4-10 local file rejection | `status="PARTIAL"`, missing `"signature"`, no sealed refs |
| `test_37` | Exact pinned OCI subject locators | SEC4-10 positive verification | `status="SUCCESS"`, seals `cosign-oci-subject` |
| `test_38` | Forged / nonlocal / mismatched OCI locators | SEC4-10 negative locators | `status="FAILED"` / `status="PARTIAL"`, fail-closed |
| `test_39` | Static tarball detached signature regression | Static tarball detached signature | `status="SUCCESS"` (`cosign`), fails on tampered bytes |

---

## 4. Test Execution & Verification

### Isolated Aggregator Suite:
Command:
```powershell
python -B -m unittest tests.unit.test_supply_chain_aggregator -v
```
Output: **39 tests passed** (0 failures, 0 errors in 5.285s).

### Isolated Model Suite:
Command:
```powershell
python -B -m unittest tests.unit.test_release_manifest_v2 -v
```
Output: **31 tests passed** (0 failures, 0 errors in 0.203s).

### Full 12-Suite Platform Regression:
Command:
```powershell
python -B -m unittest tests.unit.test_candidate_contract tests.unit.test_candidate_ingest tests.unit.test_release_manifest_v2 tests.unit.test_release_manifest tests.unit.test_registry_base tests.unit.test_oci_adapter tests.unit.test_s3_release_adapter tests.unit.test_distribution_dispatcher tests.unit.test_syft_adapter tests.unit.test_provenance_adapter tests.unit.test_cosign_adapter tests.unit.test_supply_chain_aggregator
```
Output:
```
Ran 274 tests in 25.888s
OK
```
Total: **274 tests passed** across all 12 platform test suites (0 failures, 0 errors, 0 skipped).

---

## 5. Platform Integrity & Baselines

- **Authoritative Audit Ledger:** `platform_core/audit/audit_log.jsonl` contains exactly 84 records with SHA-256 `77072d885be691c71a30514be97666a7937deb0aa87ac6f52f5490733c1ddf83` (verified byte-identical).
- **Local Terraform State:** `infrastructure/terraform/environments/local/terraform.tfstate` remains at serial 23 with 15 managed resources (verified untouched).
- **Git Commit Attribution:** Zero git commits, zero git pushes. Pre-existing working tree state is strictly preserved.
- **Cloud Spend:** $0.00. No genuine AWS credentials or external network calls.

---

## 6. Operating Posture & Stop Condition

In strict accordance with `EVALUATION-A4-PHASE-3-006` Section 20 and authorization `NERO-A4-GATE3-20261115-001`, Antigravity has published this result report atomically and stopped execution. Antigravity awaits Codex's Phase 3 re-evaluation. Phase 4 remains unassigned and has NOT been started.
