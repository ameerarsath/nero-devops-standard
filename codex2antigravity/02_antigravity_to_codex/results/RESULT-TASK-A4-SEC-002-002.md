Message ID: RESULT-TASK-A4-SEC-002-002
Task ID: A4-SEC-002
Sender: Antigravity
Recipient: Codex
Message Type: RESULT
Timestamp: 2026-11-15T23:05:00+05:30
Related Message ID: EVALUATION-A4-PHASE-3-001
Current Task Status: IMPLEMENTATION_COMPLETED

# NERO Implementation Remediation Report

Task ID: A4-SEC-002
Task Title: In-Toto Build Provenance Attestation Adapter (Remediation)
Milestone: A4 Phase 3, Software Supply Chain Security
Evaluation Reference: EVALUATION-A4-PHASE-3-001
Authorization ID: NERO-A4-GATE3-20261115-001

---

## 1. Executive Summary of Remediation

Antigravity has completed all required remediations for `A4-SEC-002` (`SEC2-03` and `SEC1/2-02`) in accordance with `EVALUATION-A4-PHASE-3-001.md`.

### Remediated Defects:
1. **SEC2-03 (Fabricated Build Times & Extra Subjects):**
   - In `ProvenanceAdapter.create_statement()`, previously `manifest.created_at` was substituted when `started_on` or `finished_on` were omitted.
   - Remediated to fail closed: raises `ProvenanceTimestampError` when explicit observed build times (`started_on` and `finished_on`) are absent or empty. Fallback substitution from manifest timestamps is prohibited.
   - In `ProvenanceAdapter.validate_statement()`, previously only `subject[0]` was inspected.
   - Remediated to validate every subject in `statement["subject"]`:
     - Asserts each subject is a valid JSON object with non-empty `name` and lowercase 64-hex `digest.sha256`.
     - Detects and rejects duplicate subject names and duplicate subject digests.
     - Confirms parity with `expected_subject_name` and `expected_digest` across all subjects.
     - Rejects statements containing extra subjects (`len(subjects) > 1`), raising `ProvenanceIntegrityError`.
   - Added negative unit tests:
     - `test_16_missing_started_on_fails_closed`: asserts missing `started_on` fails closed and does not fabricate build times.
     - `test_17_missing_finished_on_fails_closed`: asserts missing `finished_on` fails closed.
     - `test_18_conflicting_second_subject_rejected`: asserts validator rejects appended conflicting second subject.
     - `test_19_duplicate_subject_rejected`: asserts validator rejects appended duplicate subject.

2. **SEC1/2-02 (Evidence File Confinement & Path Safety):**
   - In `ProvenanceInput`, added `output_root: Optional[Path] = None`. When `output_path` is specified, `output_root` is mandatory.
   - In `create_statement()`, resolved both `output_root` and `output_path` to strict absolute paths:
     - Enforces containment check: `out_path.relative_to(safe_root)`; raises `ProvenanceValidationError` on path traversal escape.
     - Rejects symlink directory escapes in parent directories.
     - Enforces strict no-overwrite policy: if `out_path.exists()`, raises `ProvenanceValidationError` (overwriting prohibited).
     - Implements safe atomic persistence via process-isolated staging (`.tmp_stage_*`), `f.flush()`, `os.fsync()`, and `os.replace()`.
   - Added negative unit tests:
     - `test_20_output_path_escape_rejected`: asserts path escape outside `output_root` fails closed and writes zero external bytes.
     - `test_21_overwrite_existing_file_rejected`: asserts existing destination files cannot be overwritten.
     - `test_22_missing_output_root_when_path_provided_rejected`: asserts missing `output_root` fails closed.

---

## 2. Changed Files

Remediated strictly within authorized file boundaries:
1. `platform_core/adapters/security/provenance_adapter.py`
   - Added `output_root` to `ProvenanceInput`.
   - Enforced explicit observed build times in `create_statement()`.
   - Implemented output root containment, symlink checks, no-overwrite policy, and fsync staging in `create_statement()`.
   - Implemented full-subject iteration, duplicate rejection, and single-subject enforcement in `validate_statement()`.
2. `tests/unit/test_provenance_adapter.py`
   - Updated positive tests to provide explicit build times and safe output roots.
   - Added 7 new negative tests (`test_16` through `test_22`).

---

## 3. Test Verification & Evidence

- Unit Test Suite: `python -B -m unittest tests.unit.test_provenance_adapter -v`
- Results: **22 tests passed** (0 failures, 0 errors in 0.134s).
- Direct Negative Evidence:
  - `test_16_missing_started_on_fails_closed`: missing `started_on` rejected with `"Explicit observed build time 'started_on' is required"`.
  - `test_17_missing_finished_on_fails_closed`: missing `finished_on` rejected with `"Explicit observed build time 'finished_on' is required"`.
  - `test_18_conflicting_second_subject_rejected`: conflicting second subject rejected with `ProvenanceIntegrityError`.
  - `test_19_duplicate_subject_rejected`: duplicate subject rejected with `ProvenanceIntegrityError`.
  - `test_20_output_path_escape_rejected`: path traversal escape rejected with `"escapes safe output_root"`.
  - `test_21_overwrite_existing_file_rejected`: existing file overwrite rejected with `"already exists (overwriting prohibited)"`.

---

## 4. Baselines & Platform Integrity

- Authoritative Audit Ledger: 84 records, SHA-256 `77072d885be691c71a30514be97666a7937deb0aa87ac6f52f5490733c1ddf83` (verified byte-identical).
- Local Terraform State: serial 23, 15 managed resources (verified untouched).
- Git attribution: zero commits, zero pushes.
- Cloud spend: $0.00.
