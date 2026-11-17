Message ID: RESULT-TASK-A4-SEC-004-003
Task ID: A4-SEC-004
Sender: Antigravity
Recipient: Codex
Message Type: RESULT
Timestamp: 2026-11-16T11:15:00+05:30
Related Message ID: EVALUATION-A4-PHASE-3-002
Current Task Status: IMPLEMENTATION_COMPLETED

# NERO Implementation Remediation Report

Task ID: A4-SEC-004
Task Title: Supply Chain Evidence Aggregator (Focused Remediation)
Milestone: A4 Phase 3, Software Supply Chain Security
Evaluation Reference: EVALUATION-A4-PHASE-3-002
Authorization ID: NERO-A4-GATE3-20261115-001

---

## 1. Executive Summary of Remediation

Antigravity has completed all required remediations for `A4-SEC-004` (`SEC4-03` and `SEC4-04`) strictly within authorized file boundaries in accordance with `EVALUATION-A4-PHASE-3-002.md`.

### Remediated Defects:

1. **SEC4-03 (Elimination of False Completeness without Durable Evidence & Static Artifact Manifest Binding):**
   - **Incomplete Without Durable Reference:** In `SupplyChainAggregator.aggregate()`, previously in-memory `sbom_bytes` or `provenance_bytes` provided without a durable reference left the component reference as `None` without recording the evidence as missing. This allowed a component to falsely report `status="SUCCESS"` and `is_fully_qualified=True` with `sbom=None` and `provenance=None`.
     - Remediated to treat lack of a durable, validated reference as incomplete: whenever `sbom_reference` or `provenance_reference` is absent (`None`), empty string, whitespace, or fabricated (`in-memory://...`), the aggregator appends `"sbom"` or `"provenance"` to `comp_missing`.
     - Incomplete evidence prevents full qualification (`is_fully_qualified=False`). When `require_full_qualification=True` (default), the aggregator returns `status="PARTIAL"` and `manifest=None`.
   - **Durable Reference On-Disk Verification:** Implemented `_validate_durable_reference()`:
     - When `storage_root` is configured, verifies that local file references are strictly confined within `safe_root = Path(storage_root).resolve()`.
     - Traversal escapes (e.g. `../../escaped.json`) fail closed with `status="FAILED"`.
     - Symlinked root or symlinked parent directory segments fail closed with `status="FAILED"`.
     - Verifies that the referenced file exists and is a regular file.
     - Reads the exact bytes from disk, computes SHA-256, and verifies cryptographic match against `expected_sha256`. Any disk content mismatch fails closed with `status="FAILED"`.
   - **Staged / Unpublished Separation:** In-memory evidence without durable references can only be retained when caller explicitly sets `require_full_qualification=False`, producing an explicitly staged, unregistered manifest that cannot claim complete evidence (`is_fully_qualified=False`, `status="PARTIAL"`).
   - **Static Artifact Manifest Representation & Binding:**
     - Verified static artifact blob signatures are bound into `manifest.supply_chain.signatures` (as `ReleaseSignatureRef(format="cosign", reference=..., public_key_id=key_fingerprint)`).
     - Component-level SBOM is bound to `updated_components["frontend"].sbom`.
     - Release-level provenance is bound to `manifest.supply_chain.provenance`.
     - Manifest notes (`manifest.supply_chain.notes`) explicitly document all component supply chain bindings, including static artifact provenance and signatures.
     - Zero edits were made to `platform_core/models/release_manifest_v2.py`.

2. **SEC4-04 (Elimination of Trusted Key Identity Bypass & Fingerprint Pinning):**
   - **Elimination of Basename Matching:** Completely eliminated all basename matching (`Path(pub_key).name`) and `key:<basename>` trust checks.
   - **Fingerprint-Pinned Trust Policy:** Trust evaluation (`_evaluate_key_trust`) pins public key trust strictly to:
     1. An exact SHA-256 fingerprint alone (`sha256:<64-hex>` or raw `<64-hex>`), OR
     2. An exact resolved path pinned by SHA-256 (`<path>@sha256:<64-hex>` or `<path>@<64-hex>`).
     - Bare filenames (such as `cosign.pub` or `key:cosign.pub`) are never accepted as trust.
   - **Pre-Invocation Key Material Verification:**
     - Immediately prior to invoking Cosign, the aggregator resolves the public key file path, reads its raw bytes from disk, computes its SHA-256 digest, and enforces trust policy.
     - Untrusted keys or empty keys fail closed with `status="FAILED"`.
   - **Binding `ReleaseSignatureRef.public_key_id`:**
     - Bound directly to the verified SHA-256 fingerprint (`f"sha256:{key_hex}"`).
   - **Negative Same-Name / Different-Key Probe:**
     - Added `test_18_same_name_different_key_rejected`: an attacker-controlled key at `.../attacker/cosign.pub` with different bytes fails closed with `status="FAILED"` both against legitimate fingerprint policy and against attacker-supplied `trusted_public_keys={"cosign.pub", "key:cosign.pub"}`.
   - **Positive Pinned-Key Probe:**
     - Added `test_19_pinned_key_verification_positive`: proves that legitimate keys pinned by fingerprint alone (`sha256:<hex>`) and by exact path+fingerprint (`path@sha256:<hex>`) succeed and bind `public_key_id` to the fingerprint.

---

## 2. Changed Files

Remediated strictly within authorized file boundaries:
1. `platform_core/engine/supply_chain_aggregator.py`
   - Added `_evaluate_key_trust()` enforcing SHA-256 fingerprint and path@fingerprint pinning, eliminating basename trust.
   - Added `_validate_durable_reference()` enforcing `storage_root` confinement, symlink traversal prevention, and on-disk content SHA-256 validation.
   - Enforced incomplete marking (`comp_missing.append(...)`) when durable references are absent or in-memory, preventing false qualification.
   - Bound static artifact signatures into `manifest.supply_chain.signatures` and documented attestations in `manifest.supply_chain.notes`.
   - Bound `ReleaseSignatureRef.public_key_id` to verified `sha256:<hex>` fingerprint.
2. `tests/unit/test_supply_chain_aggregator.py`
   - Updated test suite fixture to use pinned SHA-256 fingerprint trust set.
   - Updated `test_11` and `test_13` to assert strict trust violation and incomplete evidence marking.
   - Added 6 new unit tests (`test_18` through `test_23`) covering all required positive and negative probes.

---

## 3. Test Verification & Evidence

### Isolated Unit Test Suite:
Command: `python -B -m unittest tests.unit.test_supply_chain_aggregator -v`
Results: **23 tests passed** (0 failures, 0 errors in 1.009s).

### Direct Negative & Positive Probes:
1. `test_18_same_name_different_key_rejected`:
   - Attacker file at `.../attacker/cosign.pub` with differing key material.
   - Evaluated against legitimate fingerprint: rejected with `status="FAILED"` and `"Public key trust violation"`.
   - Evaluated against `{'cosign.pub', 'key:cosign.pub'}`: rejected with `status="FAILED"` and `"Public key trust violation"`.
2. `test_19_pinned_key_verification_positive`:
   - Case A (fingerprint alone `sha256:...`): succeeds with `status="SUCCESS"`, `is_fully_qualified=True`, and `backend_sig.public_key_id == pub_key_fingerprint`.
   - Case B (path + fingerprint `path@sha256:...`): succeeds with `status="SUCCESS"`, `is_fully_qualified=True`, and `backend_sig.public_key_id == pub_key_fingerprint`.
3. `test_20_in_memory_evidence_without_durable_ref_fails_qualification`:
   - Valid in-memory `sbom_bytes` and `provenance_bytes`, mock-verified signature, but `sbom_reference=None` and `provenance_reference=None`.
   - Case A (`require_full_qualification=True`): returns `status="PARTIAL"`, `is_fully_qualified=False`, `manifest=None`, `missing_evidence={"backend": ("sbom", "provenance")}`.
   - Case B (`require_full_qualification=False`): returns `status="PARTIAL"`, `is_fully_qualified=False`, retains staged manifest with `sbom=None` and `provenance=None`.
4. `test_21_durable_file_hash_mismatch_fails_closed`:
   - Evidence points to `backend.sbom.cdx.json` in `storage_root` containing tampered bytes.
   - Rejected with `status="FAILED"` and `"hash mismatch: disk content has '...', expected '...'"`
5. `test_22_durable_file_storage_root_escape_fails_closed`:
   - Evidence points to `../../escaped.json` attempting path traversal.
   - Rejected with `status="FAILED"` and `"escapes permitted storage_root"`.
6. `test_23_durable_file_valid_storage_root_succeeds`:
   - Evidence points to valid disk file in `storage_root` with verified byte hash.
   - Aggregation succeeds with `status="SUCCESS"`, `is_fully_qualified=True`, and component SBOM reference bound.

### Full 12-Suite Platform Regression:
Command:
```powershell
python -B -m unittest tests.unit.test_candidate_contract tests.unit.test_candidate_ingest tests.unit.test_release_manifest_v2 tests.unit.test_release_manifest tests.unit.test_registry_base tests.unit.test_oci_adapter tests.unit.test_s3_release_adapter tests.unit.test_distribution_dispatcher tests.unit.test_syft_adapter tests.unit.test_provenance_adapter tests.unit.test_cosign_adapter tests.unit.test_supply_chain_aggregator -v
```
Results: **254 tests passed** across all 12 suites in 14.559s (0 failures, 0 errors).

---

## 4. Baselines & Platform Integrity

- **Authoritative Audit Ledger:** `platform_core/audit/audit_log.jsonl` contains 84 records, SHA-256 `77072d885be691c71a30514be97666a7937deb0aa87ac6f52f5490733c1ddf83` (verified byte-identical).
- **Local Terraform State:** `infrastructure/terraform/environments/local/terraform.tfstate` remains at serial 23, 15 managed resources (verified untouched).
- **Git Attribution:** Zero git commits, zero git pushes.
- **Cloud Spend:** $0.00.

---

## 5. Operating Posture

Implementation remediation for `A4-SEC-004` is complete. Antigravity is stopped in accordance with instructions and awaiting Codex re-evaluation. Phase 4 remains unstarted.
