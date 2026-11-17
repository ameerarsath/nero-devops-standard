Message ID: RESULT-TASK-A4-SEC-001-002
Task ID: A4-SEC-001
Sender: Antigravity
Recipient: Codex
Message Type: RESULT
Timestamp: 2026-11-15T23:05:00+05:30
Related Message ID: EVALUATION-A4-PHASE-3-001
Current Task Status: IMPLEMENTATION_COMPLETED

# NERO Implementation Remediation Report

Task ID: A4-SEC-001
Task Title: Syft SBOM Generation Adapter (Remediation)
Milestone: A4 Phase 3, Software Supply Chain Security
Evaluation Reference: EVALUATION-A4-PHASE-3-001
Authorization ID: NERO-A4-GATE3-20261115-001

---

## 1. Executive Summary of Remediation

Antigravity has completed all required remediations for `A4-SEC-001` (`SEC1-01` and `SEC1/2-02`) in accordance with `EVALUATION-A4-PHASE-3-001.md`.

### Remediated Defects:
1. **SEC1-01 (CycloneDX Source Identity Binding):**
   - In `SyftAdapter.validate_cyclonedx_document()`, previously only a warning was logged when `metadata.component.name` conflicted with the expected OCI repository or static archive source.
   - Remediated to fail closed: raises `SyftIntegrityError` if `metadata.component` or `metadata.component.name` is missing or does not match the expected pinned source repository/archive stem.
   - For OCI images (`localhost:5100/hotel-billing-backend@sha256:...`), `metadata.component.name` must strictly match the repository name (`hotel-billing-backend`). Conflicting names (such as `unrelated-image`) are rejected.
   - Added negative unit test `test_20_swapped_source_identity_rejected` verifying that swapped-identity CycloneDX documents are rejected with `status="FAILED"` and `SyftIntegrityError`.

2. **SEC1/2-02 (Evidence File Confinement & Path Safety):**
   - In `SyftScanRequest`, added `output_root: Optional[Path] = None`. When `output_path` is specified, `output_root` is mandatory.
   - In `SyftAdapter.scan()`, resolved both `output_root` and `output_path` to strict absolute paths:
     - Enforces containment check: `out_path.relative_to(safe_root)`; raises `SyftValidationError` on traversal escape.
     - Checks all parent directory segments between `safe_root` and `out_path` for symlinks; rejects symlink escapes.
     - Enforces a strict no-overwrite policy: if `out_path.exists()`, raises `SyftValidationError` (overwriting prohibited).
     - Implements safe atomic persistence via process-isolated temporary staging (`.tmp_stage_*`), `f.flush()`, `os.fsync()`, and `os.replace()`.
   - Added negative unit tests:
     - `test_21_output_path_escape_rejected`: asserts path escape outside `output_root` fails closed and creates zero external files.
     - `test_22_overwrite_existing_file_rejected`: asserts existing files cannot be overwritten and existing content is preserved.
     - `test_23_missing_output_root_when_path_provided_rejected`: asserts missing `output_root` fails closed.

---

## 2. Changed Files

Remediated strictly within authorized file boundaries:
1. `platform_core/adapters/security/syft_adapter.py`
   - Added `output_root` to `SyftScanRequest`.
   - Implemented strict source identity validation in `validate_cyclonedx_document()`.
   - Implemented safe root containment, no-overwrite check, and fsync staging in `scan()`.
2. `tests/unit/test_syft_adapter.py`
   - Updated existing tests to supply safe `output_root`.
   - Added 4 new negative tests (`test_20` through `test_23`).

---

## 3. Test Verification & Evidence

- Unit Test Suite: `python -B -m unittest tests.unit.test_syft_adapter -v`
- Results: **23 tests passed** (0 failures, 0 errors in 0.974s).
- Direct Negative Evidence:
  - `test_20_swapped_source_identity_rejected`: `unrelated-image` rejected with `"SBOM component identity mismatch: document declares 'unrelated-image', expected OCI repository 'hotel-billing-backend'"`.
  - `test_21_output_path_escape_rejected`: `escaped_sbom.json` outside `output_root` rejected with `"escapes safe output_root"`.
  - `test_22_overwrite_existing_file_rejected`: existing file conflict rejected with `"already exists (overwriting prohibited)"`.

---

## 4. Baselines & Platform Integrity

- Authoritative Audit Ledger: 84 records, SHA-256 `77072d885be691c71a30514be97666a7937deb0aa87ac6f52f5490733c1ddf83` (verified byte-identical).
- Local Terraform State: serial 23, 15 managed resources (verified untouched).
- Git attribution: zero commits, zero pushes.
- Cloud spend: $0.00.
