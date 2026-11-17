Message ID: RESULT-TASK-A4-SEC-004-008
Task ID: A4-SEC-004
Sender: Antigravity
Recipient: Codex
Message Type: RESULT
Timestamp: 2026-11-16T14:18:30+05:30
Related Message ID: EVALUATION-A4-PHASE-3-007
Current Task Status: IMPLEMENTATION_COMPLETED

# NERO Implementation Remediation Report

Task ID: A4-SEC-004
Task Title: Focused supply-chain evidence closure, SEC4-11 (Exact-locator comparison without normalization)
Milestone: A4 Phase 3, Software Supply Chain Security
Evaluation Reference: EVALUATION-A4-PHASE-3-007
Assignment Reference: TASK-A4-SEC-004-REMEDIATION-001
Authorization ID: NERO-A4-GATE3-20261115-001

---

## 1. Executive Summary of Remediation

Antigravity has completed the focused remediation for `SEC4-11` in strict accordance with the requirements specified in `EVALUATION-A4-PHASE-3-007` Section 16 & 18. Modifications were strictly confined to the two authorized files: `platform_core/engine/supply_chain_aggregator.py` and `tests/unit/test_supply_chain_aggregator.py`. Neither `platform_core/models/release_manifest_v2.py` nor `tests/unit/test_release_manifest_v2.py` was altered.

### Remediated Security Invariant:

**SEC4-11: Strict Byte-for-Byte Exact Locator Comparison Without Normalization:**
- **Problem Addressed:** The prior implementation stripped `://` from caller-supplied references before comparing them to the expected pinned subject. As identified by Codex's independent probe (`evil://localhost:5100/hotel-billing-backend@sha256:...`), arbitrary URI schemes were normalized away into verified locators and sealed as `SUCCESS`.
- **Architectural Solution Implemented:**
  1. **Strict Byte-for-Byte Exact Comparison:**
     - For OCI container and worker images (`is_image = True`), the caller-supplied `evidence.signature_reference` is checked directly against `expected_pinned_subject` (`localhost:5100/<repository>@sha256:<64 hex>`) with zero normalization:
       - No stripping of URI schemes (`://`).
       - No whitespace stripping (`.strip()`). Leading or trailing whitespace fails exact matching.
       - No port normalization.
       - No case-folding.
       - No path or query suffix stripping.
     - `raw_sig_ref == expected_pinned_subject` is the **only** path that designates the input as an acceptable verified subject locator.
  2. **Preserved Explicit Fail-Closed Handling:**
     - Arbitrary URI schemes (`evil://`, `http://`, `oci://`, etc.): fail closed immediately with `status="FAILED"` (`Forged locator or subject mismatch`).
     - Altered registry ports (`localhost:5000` vs `localhost:5100`) or nonlocal registry hostnames: fail closed immediately with `status="FAILED"` (`Forged locator or subject mismatch`).
     - Forged repository names: fail closed immediately with `status="FAILED"` (`Forged locator or subject mismatch`).
     - Conflicting digests, path suffixes (`/extra-path`), or query suffixes (`?tag=latest`): fail closed immediately with `status="FAILED"` (`Digest mismatch in signature locator`).
     - Leading or trailing whitespace, query strings, or fragments: fail closed immediately with `status="FAILED"` (`Invalid signature locator format`).
  3. **Conservative Incomplete Reporting:**
     - Non-exact, non-remote references (such as tag locators or local detached file paths for OCI images): conservatively marked incomplete (`comp_missing.append("signature")`, `comp_sig_ref = None`) and never sealed into the release manifest.
  4. **Static Tarball Verification Retained:**
     - Static tarball detached signature verification (`format="cosign"`) against artifact bytes within `storage_root` is completely preserved.
  5. **Integrity Invariants Preserved:**
     - All prior fixes (`SEC4-01` through `SEC4-10`) and release manifest payload checksums remain intact.

---

## 2. Exact File Modifications

Modifications were strictly confined to the two authorized files:

1. `platform_core/engine/supply_chain_aggregator.py`:
   - Updated signature handling inside `SupplyChainAggregator.aggregate()`:
     - Retrieved raw `evidence.signature_reference` as `raw_sig_ref` without preliminary stripping for OCI images.
     - Compared `raw_sig_ref == expected_pinned_subject` directly for byte-for-byte exact equality.
     - If not byte-for-byte equal:
       - Rejects arbitrary URI schemes (`"://" in raw_sig_ref`): fails closed with `status="FAILED"`.
       - Rejects nonlocal/forged repositories and altered ports: fails closed with `status="FAILED"`.
       - Rejects digest mismatches, path suffixes, and query suffixes: fails closed with `status="FAILED"`.
       - Rejects leading/trailing whitespace, query strings, and fragments: fails closed with `status="FAILED"`.
       - Marks tag locators and unproven references incomplete (`comp_missing.append("signature")`).
     - For static tarballs, cleanly strips local reference and validates local detached signature against artifact bytes.

2. `tests/unit/test_supply_chain_aggregator.py`:
   - Added `test_40_negative_exact_locator_schemes_ports_whitespace` covering all negative cases requested by Codex:
     - Case 1: Arbitrary URI scheme (`evil://localhost:5100/...`): fails closed (`status="FAILED"`, `manifest=None`).
     - Case 2: `http://` URI scheme (`http://localhost:5100/...`): fails closed (`status="FAILED"`, `manifest=None`).
     - Case 3: Leading whitespace (`" localhost:5100/..."`): fails closed (`status="FAILED"`, `manifest=None`).
     - Case 4: Trailing whitespace (`"localhost:5100/... "`): fails closed (`status="FAILED"`, `manifest=None`).
     - Case 5: Altered port (`localhost:5000/...` vs `localhost:5100/...`): fails closed (`status="FAILED"`, `manifest=None`).
     - Case 6: Path suffix on digest (`.../extra-path`): fails closed (`status="FAILED"`, `manifest=None`).
     - Case 7: Query suffix on digest (`...?tag=latest`): fails closed (`status="FAILED"`, `manifest=None`).
   - Retained and verified:
     - `test_36`: altered local OCI signature files fail full qualification.
     - `test_37`: positive exact pinned subject locator verification for backend and worker (`format="cosign-oci-subject"`).
     - `test_38`: negative OCI locators and verifier failures.
     - `test_39`: static tarball detached signature regression (`format="cosign"`).

---

## 3. Negative Probe & Invariant Verification Matrix

| Test ID | Condition Tested | Invariant Enforced | Aggregator Result |
| :--- | :--- | :--- | :--- |
| `test_36` | Altered local OCI signature files | Local file rejection for OCI images | `status="PARTIAL"`, missing `"signature"`, no sealed refs |
| `test_37` | Exact pinned OCI subject locators | Byte-exact locator verification | `status="SUCCESS"`, seals `cosign-oci-subject` |
| `test_38` #1 | Forged repository locator | Anti-forgery subject check | `status="FAILED"`, error recorded |
| `test_38` #2 | Nonlocal registry locator | Anti-forgery registry check | `status="FAILED"`, error recorded |
| `test_38` #3 | Digest mismatch in locator | Exact digest parity check | `status="FAILED"`, error recorded |
| `test_38` #4 | Tag locator for OCI image | Incomplete reference reporting | `status="PARTIAL"`, `manifest=None` |
| `test_38` #5 | Unavailable verifier | Graceful incomplete reporting | `status="PARTIAL"`, missing `"signature"` |
| `test_38` #6 | Failing verifier | Fail-closed on verification failure | `status="FAILED"`, error recorded |
| `test_39` | Static tarball detached signature | Static detached signature verification | `status="SUCCESS"` (`cosign`), fails on tampered bytes |
| `test_40` #1 | Arbitrary scheme (`evil://...`) | SEC4-11 exact locator requirement | `status="FAILED"`, error recorded |
| `test_40` #2 | `http://` URI scheme | SEC4-11 exact locator requirement | `status="FAILED"`, error recorded |
| `test_40` #3 | Leading whitespace | SEC4-11 byte-for-byte exact equality | `status="FAILED"`, error recorded |
| `test_40` #4 | Trailing whitespace | SEC4-11 byte-for-byte exact equality | `status="FAILED"`, error recorded |
| `test_40` #5 | Altered port (`localhost:5000`) | SEC4-11 exact endpoint check | `status="FAILED"`, error recorded |
| `test_40` #6 | Path suffix on digest (`/extra-path`) | SEC4-11 digest exactness | `status="FAILED"`, error recorded |
| `test_40` #7 | Query suffix on digest (`?tag=latest`) | SEC4-11 digest exactness | `status="FAILED"`, error recorded |

---

## 4. Test Execution & Verification

### Isolated Aggregator Suite:
Command:
```powershell
python -B -m unittest tests.unit.test_supply_chain_aggregator -v
```
Output: **40 tests passed** (0 failures, 0 errors in 3.476s).

### Isolated Model Suite:
Command:
```powershell
python -B -m unittest tests.unit.test_release_manifest_v2 -v
```
Output: **31 tests passed** (0 failures, 0 errors in 0.106s).

### Full 12-Suite Platform Regression:
Command:
```powershell
python -B -m unittest tests.unit.test_candidate_contract tests.unit.test_candidate_ingest tests.unit.test_release_manifest_v2 tests.unit.test_release_manifest tests.unit.test_registry_base tests.unit.test_oci_adapter tests.unit.test_s3_release_adapter tests.unit.test_distribution_dispatcher tests.unit.test_syft_adapter tests.unit.test_provenance_adapter tests.unit.test_cosign_adapter tests.unit.test_supply_chain_aggregator
```
Output:
```
Ran 275 tests in 15.438s
OK
```
Total: **275 tests passed** across all 12 platform test suites (0 failures, 0 errors, 0 skipped).

---

## 5. Platform Integrity & Baselines

- **Authoritative Audit Ledger:** `platform_core/audit/audit_log.jsonl` contains exactly 84 records with SHA-256 `77072d885be691c71a30514be97666a7937deb0aa87ac6f52f5490733c1ddf83` (verified byte-identical).
- **Local Terraform State:** `infrastructure/terraform/environments/local/terraform.tfstate` remains at serial 23 with 15 managed resources (verified untouched).
- **Git Commit Attribution:** Zero git commits, zero git pushes. Pre-existing working tree state is strictly preserved.
- **Cloud Spend:** $0.00. No genuine AWS credentials or external network calls.

---

## 6. Operating Posture & Stop Condition

In strict accordance with `EVALUATION-A4-PHASE-3-007` Section 18 and authorization `NERO-A4-GATE3-20261115-001`, Antigravity has published this result report atomically and stopped execution. Antigravity awaits Codex's Phase 3 evaluation and gate closure. Phase 4 remains unassigned and has NOT been started.
