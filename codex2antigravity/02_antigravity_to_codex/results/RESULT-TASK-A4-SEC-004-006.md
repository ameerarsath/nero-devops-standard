Message ID: RESULT-TASK-A4-SEC-004-006
Task ID: A4-SEC-004
Sender: Antigravity
Recipient: Codex
Message Type: RESULT
Timestamp: 2026-11-16T12:35:00+05:30
Related Message ID: EVALUATION-A4-PHASE-3-005
Current Task Status: IMPLEMENTATION_COMPLETED

# NERO Implementation Remediation Report

Task ID: A4-SEC-004
Task Title: Focused supply-chain evidence closure, SEC4-08 and SEC4-09
Milestone: A4 Phase 3, Software Supply Chain Security
Evaluation Reference: EVALUATION-A4-PHASE-3-005
Assignment Reference: TASK-A4-SEC-004-REMEDIATION-001
Authorization ID: NERO-A4-GATE3-20261115-001

---

## 1. Executive Summary of Remediation

Antigravity has completed the scoped remediations for `SEC4-08` and `SEC4-09` strictly within the two authorized files: `platform_core/engine/supply_chain_aggregator.py` and `tests/unit/test_supply_chain_aggregator.py`. Neither `platform_core/models/release_manifest_v2.py` nor `tests/unit/test_release_manifest_v2.py` was altered.

### Remediated Security Invariants:

1. **SEC4-08: Conservative Incomplete Handling for Remote OCI Signature References:**
   - In `SupplyChainAggregator.aggregate()`:
     - Remote OCI signature references (`_is_remote_reference(sig_ref)`) continue to undergo subject-alignment anti-forgery validation against the component subject and distribution receipt storage reference. Mismatched or conflicting references fail closed immediately with `status="FAILED"`.
     - Key trust evaluation (`_evaluate_key_trust`) and Cosign verification continue to fail closed if the key is untrusted or if cryptographic verification fails.
     - When Cosign verification of an OCI image subject succeeds, `CosignAdapter.verify()` builds and runs `cosign verify --key ... <subject>` which proves the repository image digest subject, but does NOT independently prove the exact caller-supplied remote signature reference string (`sig_ref`).
     - Because no independent exact-reference resolver contract exists within the authorized scope, the aggregator conservatively treats remote OCI signature references as incomplete (`comp_missing.append("signature")`, `comp_sig_ref = None`) rather than sealing an unproven reference into the manifest.
     - Valid local detached-signature verification remains fully available: verified local signature references are sealed into `manifest.components` and `manifest.supply_chain.signatures`.

2. **SEC4-09: Pre-Resolution Lexical Symlink Validation:**
   - Introduced `_validate_local_path(ref, storage_root, context) -> Tuple[Optional[Path], Optional[str]]` in `platform_core/engine/supply_chain_aggregator.py`:
     - Checks `storage_root` itself and rejects if it is a symlink.
     - Inspects each incremental lexical path segment from `safe_root` down through the target file *before* calling `resolve()`.
     - Rejects any leaf symlink or intermediate directory symlink before resolution, preventing hidden in-root symlink traversal where `resolve()` would otherwise mask symlink targets.
     - Also validates the normalized lexical path before resolution.
     - Resolves the target after all pre-resolution checks pass and enforces strict lexical containment within `safe_root` via `resolved_target.relative_to(safe_root)`.
     - Confirms target file exists, is a regular file, and verifies disk bytes match expected SHA-256.
   - Applied consistently across local SBOM, build provenance (`_validate_durable_reference`), and local detached signature verification in `SupplyChainAggregator.aggregate()`.

---

## 2. Exact File Modifications

Modifications were strictly confined to the two authorized files:

1. `platform_core/engine/supply_chain_aggregator.py`:
   - Added `_validate_local_path()` helper implementing strict pre-resolution lexical symlink inspection on both leaf and directory components, resolved root confinement, existence, regular file checks, and clear failure-closed error reporting.
   - Updated `_validate_durable_reference()` to delegate local path resolution and symlink inspection to `_validate_local_path()`, followed by disk byte SHA-256 verification.
   - Updated `SupplyChainAggregator.aggregate()` local signature validation to call `_validate_local_path()` before reading signature bytes.
   - Updated `SupplyChainAggregator.aggregate()` remote signature verification (SEC4-08): if `is_remote_sig` is True, Cosign verification evaluates the image subject, but does not seal `sig_ref` into the manifest; instead, it conservatively marks `comp_missing.append("signature")` and leaves `comp_sig_ref = None`.

2. `tests/unit/test_supply_chain_aggregator.py`:
   - Updated `test_30`:
     - Case C: Asserts that subject-aligned remote signature references conservatively report incomplete (`status="PARTIAL"`, `is_fully_qualified=False`, `manifest=None` when `require_full_qualification=True`, with `"signature"` in `missing_evidence`).
     - Case D: Asserts that when `require_full_qualification=False`, the manifest stages unregistered with `signature=None` on the component.
   - Added `test_33_symlink_leaf_rejected_before_resolution`:
     - Tests that an SBOM reference pointing to a leaf symlink within `storage_root` is rejected before resolution.
   - Added `test_34_symlink_parent_directory_rejected_before_resolution`:
     - Tests that a provenance reference traversing an intermediate directory symlink within `storage_root` is rejected before resolution.
   - Added `test_35_local_signature_symlink_rejected_before_resolution`:
     - Tests that a local detached signature reference that is a symlink within `storage_root` is rejected before resolution.

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
| `test_30` Case C | Remote OCI signature (subject-aligned) | SEC4-08 unproven ref incomplete | `status="PARTIAL"`, `manifest=None` |
| `test_30` Case D | Remote OCI signature (`require_full=False`) | SEC4-08 staged without unproven ref | `status="PARTIAL"`, `comp.signature=None` |
| `test_33` | Leaf symlink in `storage_root` | SEC4-09 pre-resolution lexical check | `status="FAILED"`, symlink rejected |
| `test_34` | Parent dir symlink in `storage_root` | SEC4-09 pre-resolution lexical check | `status="FAILED"`, symlink rejected |
| `test_35` | Local signature symlink in `storage_root` | SEC4-09 pre-resolution lexical check | `status="FAILED"`, symlink rejected |

---

## 4. Host OS Symlink Limitation & Platform-Independent Testing

On the Windows development host, live symlink creation raises:
```
OSError: [WinError 1314] A required privilege is not held by the client
```
In accordance with Codex's instructions in `EVALUATION-A4-PHASE-3-005` Section 19:
- Tests 33, 34, and 35 first attempt to create a real filesystem symlink via `os.symlink()`.
- If the host raises `OSError` or `NotImplementedError` due to OS privilege constraints, the tests cleanly engage a platform-independent fallback using `unittest.mock.patch.object(Path, "is_symlink", ...)` matching the target path.
- The tests verify that `_validate_local_path()` inspects the lexical path segments before calling `resolve()`, catching the symlink and failing closed with `status="FAILED"` and an explicit symlink error message.

---

## 5. Test Execution & Verification

### Isolated Aggregator Suite:
Command:
```powershell
python -B -m unittest tests.unit.test_supply_chain_aggregator -v
```
Output: **35 tests passed** (0 failures, 0 errors in 4.142s).

### Isolated Model Suite:
Command:
```powershell
python -B -m unittest tests.unit.test_release_manifest_v2 -v
```
Output: **31 tests passed** (0 failures, 0 errors in 0.176s).

### Full 12-Suite Platform Regression:
Command:
```powershell
python -B -m unittest tests.unit.test_candidate_contract tests.unit.test_candidate_ingest tests.unit.test_release_manifest_v2 tests.unit.test_release_manifest tests.unit.test_registry_base tests.unit.test_oci_adapter tests.unit.test_s3_release_adapter tests.unit.test_distribution_dispatcher tests.unit.test_syft_adapter tests.unit.test_provenance_adapter tests.unit.test_cosign_adapter tests.unit.test_supply_chain_aggregator
```
Output:
```
Ran 270 tests in 23.055s
OK
```
Total: **270 tests passed** across all 12 platform test suites (0 failures, 0 errors, 0 skipped).

---

## 6. Platform Integrity & Baselines

- **Authoritative Audit Ledger:** `platform_core/audit/audit_log.jsonl` contains exactly 84 records with SHA-256 `77072d885be691c71a30514be97666a7937deb0aa87ac6f52f5490733c1ddf83` (verified byte-identical).
- **Local Terraform State:** `infrastructure/terraform/environments/local/terraform.tfstate` remains at serial 23 with 15 managed resources (verified untouched).
- **Git Commit Attribution:** Zero git commits, zero git pushes. Pre-existing working tree state is strictly preserved.
- **Cloud Spend:** $0.00. No genuine AWS credentials or external network calls.

---

## 7. Operating Posture & Stop Condition

In strict accordance with `EVALUATION-A4-PHASE-3-005` Section 21 and authorization `NERO-A4-GATE3-20261115-001`, Antigravity has published this result report atomically and stopped execution. Antigravity awaits Codex's Phase 3 re-evaluation. Phase 4 remains unassigned and has NOT been started.
