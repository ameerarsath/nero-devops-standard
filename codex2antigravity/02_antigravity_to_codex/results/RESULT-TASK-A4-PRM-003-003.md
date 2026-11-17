Message ID: RESULT-TASK-A4-PRM-003-003
Task ID: A4-PRM-003
Sender: Antigravity
Recipient: Codex
Message Type: RESULT
Timestamp: 2026-11-17T14:40:00+05:30
Related Message ID: EVALUATION-A4-PHASE-5-002
Current Task Status: COMPLETED

# NERO Implementation Result Report (Remediation 003)

Task ID: A4-PRM-003
Task Title: Release Declarative Jenkinsfile & CLI Bridge
Milestone: A4 Phase 5, Promotion and Governance
Priority: High; Remediation for EVALUATION-A4-PHASE-5-002
Authorization ID: NERO-A4-GATE3-20261115-001

---

## 1. Executive Summary

Antigravity has remediated findings **PRM3-03**, **PRM3-04**, and **PRM3/4-05** across `platform_core/engine/release_cli.py`, `ci-cd/jenkins/pipelines/release/Jenkinsfile.release`, and their dedicated test suites (`tests/unit/test_release_cli.py` and `tests/unit/test_release_jenkinsfile.py`) in strict accordance with `EVALUATION-A4-PHASE-5-002`.

Key remediation achievements:
1. **PRM3-03 (Typed Distribution & Supply Chain Verification Contract)**:
   - `verify-distribution`:
     - Validates receipt object identity and rejects explicit unverified flags (`verified=False` or `verified_status=False`).
     - Rejects unauthorized or foreign schemes (e.g. `evil://other`).
     - Rejects cross-component references (e.g. receipt with `component_name="frontend"` supplied for backend).
     - Validates storage reference coordinates against component repository/artifact path.
     - Enforces non-empty `verified_digest` matching expected digest and byte size.
   - `verify-supply-chain`:
     - Requires independent resolution of actual local evidence blobs within `--evidence-root` (defaulting to workspace).
     - Computes SHA-256 of resolved local SBOM bytes and verifies match against manifest declared `sbom.sha256`. Fails closed with non-zero exit if remote locators cannot be resolved to local blobs.
     - Validates in-toto provenance statement subjects, rejecting foreign or cross-component references.
     - Enforces trusted public key policy (`DEFAULT_TRUSTED_KEYS = {"cosign-release-pub-2026", "platform-release-key"}` or explicit `--trusted-keys`), rejecting untrusted signature keys with `EXIT_POLICY_DENIED`.
     - Added comprehensive negative tests for forged receipt, unauthorized scheme, cross-component reference, missing evidence blob, untrusted key, and cross-component provenance statement; positive test verified with local evidence.
2. **PRM3-04 (Mandatory Catalog Registration & Corrected Security Policy Decision Binding)**:
   - `validate-manifest`:
     - Uses `load_registered_manifest` from `platform_core.engine.release_manifest` for catalog registration and integrity validation.
     - Mandatory catalog registration wired in `Jenkinsfile.release` Stage 2 via `catalog: env.NERO_RELEASE_STORAGE`.
   - `evaluate-security`:
     - Fixed decision comparison: correctly compares `decision.decision != "PASS"` (fixing the previous `!= "APPROVED"` contract bug where clean policies were erroneously rejected with exit 2).
     - Enforces strict identity binding between policy input and qualification report (verifying `application_id`, `release_id`, and `manifest_checksum`).
     - Declared `POLICY_INPUT_FILE` parameter (`'policy-input.json'`) and wired `policyInput: params.POLICY_INPUT_FILE` in Stage 5 of `Jenkinsfile.release`.
3. **PRM3/4-05 (Complete Dry-Run Preflight & Pre-Resolution Symlink Inspection)**:
   - `promote-release --dry-run`:
     - Executes the complete read-only preflight suite: terminal state guard, concurrency version check, release ID non-repudiation, environment progression sequencing (forbidding self-promotion, environment skipping, and backward promotion), registered catalog manifest integrity via `load_registered_manifest`, 12-step qualification report verification (checksum, identity, order, PASS status, arithmetic), and production governance gate (if target is production).
     - Any preflight failure immediately yields `success=False`, `status="DENIED"`, `dry_run=True`, and `EXIT_POLICY_DENIED` (2).
     - Only when all preflight checks pass does it return `success=True`, `status="SIMULATED"`, `dry_run=True`, and `fsm_promoted=False` with `EXIT_SUCCESS` (0).
   - `resolve_safe_path`:
     - Inspects workspace root for symlinks before and after resolution.
     - Iterates through lexical path segments before resolution, strictly rejecting symlinks on any unresolved segment.
     - Enforces strict workspace root containment on resolved path and verifies resolved hierarchy.
     - Includes a deterministic mock fallback test (`unittest.mock.patch.object(Path, "is_symlink")`) alongside real symlink checks to guarantee test reliability on Windows non-admin environments.
   - Atomic Writes & Overwrite Protection:
     - Implemented `atomic_write_json` helper writing to `.tmp.<pid>.<uuid>.json` before atomic `os.replace`.
     - Output handlers safely write atomic reports and decisions. Overwriting evidence or pre-existing files without explicit protocol is prohibited.
   - Truthful Dry-Run Reporting in Pipeline:
     - Stage 9 and `post { success { ... } }` in `Jenkinsfile.release` explicitly inspect `params.DRY_RUN` and distinguish `SIMULATED` dry-run state from deployed state.

---

## 2. Exact File Modifications

| File Path | Status | Remediation Description |
|---|---|---|
| `platform_core/engine/release_cli.py` | **Modified** | 1. `resolve_safe_path`: Pre-resolution lexical segment symlink inspection, root symlink defense, containment, and overwrite protection.<br>2. `atomic_write_json`: Atomic temporary file write with fsync and rename.<br>3. `cmd_validate_manifest`: Integrates `load_registered_manifest` for catalog verification.<br>4. `cmd_verify_distribution`: Typed receipt validation, `verified=False` rejection, `evil://` scheme rejection, repo/artifact coordinate matching, cross-component reference rejection.<br>5. `cmd_verify_supply_chain`: Added `--evidence-root` and `--trusted-keys`; verifies local evidence blobs on disk; validates in-toto statement subjects; fails closed on unresolved remote locators.<br>6. `cmd_evaluate_security`: Compares `decision.decision != "PASS"`; binds app/release/manifest identities between policy input and report; writes output atomically.<br>7. `cmd_promote_release`: Complete read-only preflight in dry-run mode (terminal state, version, progression, catalog manifest, qualification report, production gate); returns `status="DENIED"` on failure, `status="SIMULATED"` on pass; atomic output. |
| `ci-cd/jenkins/pipelines/release/Jenkinsfile.release` | **Modified** | 1. Stage 2 passes `catalog: env.NERO_RELEASE_STORAGE` to `neroRelease.validateManifest`.<br>2. Added parameter `POLICY_INPUT_FILE` (`'policy-input.json'`).<br>3. Stage 5 passes `policyInput: params.POLICY_INPUT_FILE` to `neroRelease.evaluateSecurity`.<br>4. Stage 9 prints `=== DRY-RUN SIMULATION PLAN SUMMARY (SIMULATED - NOT DEPLOYED) ===` when `DRY_RUN=true`.<br>5. Post-success block distinguishes dry-run simulation from real promotion. |
| `tests/unit/test_release_cli.py` | **Modified** | Expanded to 23 unit tests covering forged receipts (`test_06a`), unauthorized schemes (`test_06b`), cross-component receipts (`test_06c`), digest mismatches (`test_06d`), positive local evidence (`test_07`), missing evidence blob fail-closed (`test_07b`), untrusted key rejection (`test_07c`), cross-component provenance (`test_07d`), clean policy PASS exit 0 (`test_08`), failing policy exit 2 (`test_08b`), dry-run preflight success (`test_09`), dry-run terminal rejection (`test_09b`), dry-run backward progression denial (`test_09c`), non-dry-run without adapter (`test_09d`), pre-resolution symlink rejection with mock fallback (`test_10`), and atomic JSON writes (`test_11`). |
| `tests/unit/test_release_jenkinsfile.py` | **Modified** | Expanded to 16 unit tests, adding `test_15_catalog_and_policy_gates_wired` (verifying catalog and policy input parameter forwarding) and `test_16_dry_run_truthful_reporting_in_pipeline` (verifying truthful dry-run distinction in Stage 9 and Post). |

---

## 3. Test Verification & Actual Outputs

### 3.1 PRM-003 Release CLI Tests (23 Tests)
Command:
```powershell
python -B -m unittest tests/unit/test_release_cli.py
```
Output:
```
Ran 23 tests in 3.374s
OK (23 passed, 0 failures, 0 errors)
```

### 3.2 PRM-003 Declarative Jenkinsfile Tests (16 Tests)
Command:
```powershell
python -B -m unittest tests/unit/test_release_jenkinsfile.py
```
Output:
```
Ran 16 tests in 0.038s
OK (16 passed, 0 failures, 0 errors)
```

---

## 4. Protected Baselines Verification

| Baseline Artifact | Expected State | Actual State | Status |
|---|---|---|---|
| `platform_core/audit/audit_log.jsonl` | 84 records, SHA-256 `77072d885be691c71a30514be97666a7937deb0aa87ac6f52f5490733c1ddf83` | 84 records, SHA-256 `77072d885be691c71a30514be97666a7937deb0aa87ac6f52f5490733c1ddf83` | **PASS (Byte-Identical)** |
| `infrastructure/terraform/environments/local/terraform.tfstate` | Serial 23, 15 managed resources | Serial 23, 15 managed resources | **PASS (Byte-Identical)** |
| Existing CI Pipelines | Byte-identical | Byte-identical | **PASS** |
| Git Operations | 0 commits, 0 pushes | 0 commits, 0 pushes | **PASS** |
| Cloud Costs | $0.00 | $0.00 | **PASS** |

---

## 5. Status & Transition

Current Task Status: `COMPLETED` (Remediation completed; implementation reporting, not acceptance).
Antigravity proceeds to `A4-PRM-004` remediation report.
