Message ID: RESULT-TASK-A4-MAN-001-003
Task ID: A4-MAN-001
Sender: Antigravity
Recipient: Codex
Message Type: RESULT
Timestamp: 2026-11-15T01:08:00+05:30
Related Message ID: EVALUATION-TASK-A4-MAN-001-002
Current Task Status: IMPLEMENTATION_COMPLETED

# NERO Implementation Remediation Result Report (Follow-Up 003)

Task ID: A4-MAN-001
Task Title: Universal Release Manifest v2 Schema (Focused MAN-02 Remediation)
Milestone: A4 Milestone 1, Candidate Ingestion and Release Manifest Architecture
Authorization ID: NERO-A4-MAN-001-TASK-AUTH-20261114-001
Evaluation Reference: EVALUATION-TASK-A4-MAN-001-002

---

## 1. Executive Summary

In response to the independent evaluation `EVALUATION-TASK-A4-MAN-001-002`, Antigravity has completed the focused correction for the remaining `MAN-02` legacy static artifact path handling.

All modifications remain strictly within the authorized implementation files:
1. `platform_core/models/release_manifest_v2.py`
2. `tests/unit/test_release_manifest_v2.py`
3. `platform_core/models/__init__.py`

All 27 unit tests in `tests/unit/test_release_manifest_v2.py` passed (expanded with dedicated legacy unsafe path regression tests).
All 88 tests across the combined regression suite passed.
The authoritative audit ledger remains untouched at 84 records (SHA-256: `77072D885BE691C71A30514BE97666A7937DEB0AA87AC6F52F5490733C1DDF83`).
The local Terraform state remains untouched at Serial 23 (15 managed resources).
Zero Git commits or pushes were made. Programme Gate 3 remains pending; A4-MAN-002 and subsequent tasks remain unauthorized.

---

## 2. Targeted MAN-02 Remediation Details

### Defect Identified in EVALUATION-TASK-A4-MAN-001-002
In `from_legacy_manifest()`, when processing static components (e.g. `c_data["artifact"]`), the converter previously attempted basename and suffix salvage if the path started with `/` or matched a drive letter (e.g. extracting `releases/` suffix or returning `Path(clean_path).name`). Consequently, an otherwise complete legacy payload containing `/other-app/private.tar.gz` was silently rewritten to `private.tar.gz` and accepted, modifying source evidence and bypassing unsafe path rejection.

### Remediation Applied
1. **Basename and Suffix Salvage Completely Removed:**
   In `platform_core/models/release_manifest_v2.py` (lines 824-837), all salvage heuristics (`Path(clean_path).name` and `clean_path.split("releases/", 1)[1]`) have been removed.
2. **Strict Direct Validation & Fail-Closed Migration Error:**
   `raw_art_path` is passed directly to `StaticTarballComponent(artifact_path=raw_art_path, ...)`. Any path violating safe relative storage key rules (null bytes, absolute paths, drive letters, UNC shares, traversal segments `..` or `.`, and empty segments) triggers a validation error and is caught to immediately raise `LegacyManifestMigrationError` identifying the offending component and path:
   ```python
   try:
       components[c_name] = StaticTarballComponent(
           name=c_name,
           artifact_path=raw_art_path,
           sha256=sha,
           size_bytes=int(size)
       )
   except (ValueError, ValidationError) as e:
       raise LegacyManifestMigrationError(
           f"Cannot migrate legacy manifest: unsafe static artifact path '{raw_art_path}' "
           f"in component '{c_name}': {e}"
       ) from e
   ```
3. **Preservation of Ordinary Relative Artifact Names:**
   Genuinely safe relative keys (e.g. `frontend-dist-rel-20261108133349.tar.gz`, `releases/frontend-dist.tar.gz`, `assets/subfolder/bundle.tar.gz`) pass through without modification.
4. **Targeted Regression Suite:**
   Added `test_26_legacy_conversion_rejects_unsafe_artifact_paths` to `tests/unit/test_release_manifest_v2.py`. Using an otherwise complete legacy payload, it asserts `LegacyManifestMigrationError` is raised for:
   - Absolute Unix paths: `/other-app/private.tar.gz`, `/absolute/secret.tar.gz`
   - Windows drive paths: `C:/secret.tar.gz`, `D:\secret.tar.gz`
   - UNC network paths: `//unc-share/secret.tar.gz`, `\\unc-share\secret.tar.gz`
   - Directory traversal: `../other-app/secret.tar.gz`, `releases/app/../../etc/passwd`
   - Empty path segments: `releases//empty/path.tar.gz`
   - Null bytes: `releases/\0evil.tar.gz`
   And verifies that safe relative paths convert successfully.

---

## 3. Verification Commands and Exact Test Evidence

### Command 1: Isolated Release Manifest v2 Suite
```powershell
python -B -m unittest tests.unit.test_release_manifest_v2 -v
```
**Output:**
```text
test_01_valid_single_component_oci_manifest (tests.unit.test_release_manifest_v2.TestReleaseManifestV2) ... ok
test_02_valid_multi_component_manifest (tests.unit.test_release_manifest_v2.TestReleaseManifestV2) ... ok
test_03_valid_worker_queue_component (tests.unit.test_release_manifest_v2.TestReleaseManifestV2) ... ok
test_04_invalid_oci_digest (tests.unit.test_release_manifest_v2.TestReleaseManifestV2) ... ok
test_05_missing_payload_checksum_fails_closed (tests.unit.test_release_manifest_v2.TestReleaseManifestV2) ... ok
test_06_mismatched_payload_checksum_fails_closed (tests.unit.test_release_manifest_v2.TestReleaseManifestV2) ... ok
test_07_malformed_semver_tag_rejected (tests.unit.test_release_manifest_v2.TestReleaseManifestV2) ... ok
test_08_negative_or_zero_static_artifact_size_rejected (tests.unit.test_release_manifest_v2.TestReleaseManifestV2) ... ok
test_09_invalid_git_commit_sha_rejected (tests.unit.test_release_manifest_v2.TestReleaseManifestV2) ... ok
test_10_component_name_mismatch_rejected (tests.unit.test_release_manifest_v2.TestReleaseManifestV2) ... ok
test_11_empty_components_rejected (tests.unit.test_release_manifest_v2.TestReleaseManifestV2) ... ok
test_12_unsafe_static_paths_rejected (tests.unit.test_release_manifest_v2.TestReleaseManifestV2) ... ok
test_13_safe_static_paths_accepted (tests.unit.test_release_manifest_v2.TestReleaseManifestV2) ... ok
test_14_insertion_order_checksum_stability (tests.unit.test_release_manifest_v2.TestReleaseManifestV2) ... ok
test_15_tampering_component_invalidates_checksum (tests.unit.test_release_manifest_v2.TestReleaseManifestV2) ... ok
test_16_tampering_metadata_invalidates_checksum (tests.unit.test_release_manifest_v2.TestReleaseManifestV2) ... ok
test_17_deep_immutability_enforced (tests.unit.test_release_manifest_v2.TestReleaseManifestV2) ... ok
test_18_output_serialization_gated_against_tampered_state (tests.unit.test_release_manifest_v2.TestReleaseManifestV2) ... ok
test_19_valid_candidate_conversion (tests.unit.test_release_manifest_v2.TestReleaseManifestV2) ... ok
test_20_candidate_tag_matching_and_mismatch (tests.unit.test_release_manifest_v2.TestReleaseManifestV2) ... ok
test_21_candidate_conversion_fails_on_tampered_candidate (tests.unit.test_release_manifest_v2.TestReleaseManifestV2) ... ok
test_22_complete_legacy_conversion_preserves_source_repo_and_refs (tests.unit.test_release_manifest_v2.TestReleaseManifestV2) ... ok
test_23_legacy_conversion_no_silent_invention (tests.unit.test_release_manifest_v2.TestReleaseManifestV2) ... ok
test_24_checked_in_incomplete_legacy_fails_without_migration_inputs (tests.unit.test_release_manifest_v2.TestReleaseManifestV2) ... ok
test_25_legacy_conversion_detects_component_conflicts (tests.unit.test_release_manifest_v2.TestReleaseManifestV2) ... ok
test_26_legacy_conversion_rejects_unsafe_artifact_paths (tests.unit.test_release_manifest_v2.TestReleaseManifestV2) ... ok
test_27_serialization_round_trip (tests.unit.test_release_manifest_v2.TestReleaseManifestV2) ... ok

----------------------------------------------------------------------
Ran 27 tests in 0.110s

OK
```

### Command 2: Combined Regression Suite
```powershell
python -B -m unittest tests.unit.test_candidate_contract tests.unit.test_candidate_ingest tests.unit.test_release_manifest_v2 -q
```
**Output:**
```text
Quarantined uncommitted orphan staged candidate: cand-hotel-billing-orphan-crash -> C:\Users\moham\AppData\Local\Temp\tmpxvcyf0vy\staging\.orphans\cand-hotel-billing-orphan-crash.json.staged.1794684926
Quarantined uncommitted orphan staged candidate: cand-hotel-billing-20261113100026 -> C:\Users\moham\AppData\Local\Temp\tmprc5s3y4s\staging\.orphans\cand-hotel-billing-20261113100026.json.staged.1794684926
Quarantined un-audited candidate from consumer namespace: cand-hotel-billing-20261113100027
----------------------------------------------------------------------
Ran 88 tests in 4.042s

OK
```

---

## 4. Baseline and Invariant Integrity

1. **Authoritative Audit Ledger Count:** Exactly 84 records (verified unchanged).
2. **Authoritative Audit Ledger SHA-256:** `77072D885BE691C71A30514BE97666A7937DEB0AA87AC6F52F5490733C1DDF83` (verified identical).
3. **Local Terraform State:** Serial 23, 15 managed resources (verified unchanged).
4. **Cloud Spend / Network Side Effects:** $0.00 cloud spend; zero external API or network calls; zero mutations to live Docker/Floci infrastructure.
5. **Version Control:** Zero Git commits, zero Git pushes.

---

## 5. Scope Adherence and Governance Status

- **Task Scope:** Strictly limited to `A4-MAN-001` under authorization `NERO-A4-MAN-001-TASK-AUTH-20261114-001`.
- **Files Modified:**
  - `platform_core/models/release_manifest_v2.py`
  - `tests/unit/test_release_manifest_v2.py`
  - `platform_core/models/__init__.py`
- **Subsequent Tasks:** `A4-MAN-002` and all subsequent tasks remain strictly unauthorized.
- **Programme Gates:** Programme Gate 3 remains pending owner authorization.
- **Current Status:** `IMPLEMENTATION_COMPLETED`. Codex is requested to make the final acceptance evaluation on `A4-MAN-001`.
