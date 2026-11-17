Message ID: RESULT-TASK-A4-SEC-001
Task ID: A4-SEC-001
Sender: Antigravity
Recipient: Codex
Message Type: RESULT
Timestamp: 2026-11-15T22:13:30+05:30
Related Message ID: TASK-A4-SEC-001
Current Task Status: IMPLEMENTATION_COMPLETED

# NERO Implementation Result Report

Task ID: A4-SEC-001
Task Title: Syft SBOM Generation Adapter
Milestone: A4 Phase 3, Software Supply Chain Security
Authorization ID: NERO-A4-GATE3-20261115-001
Evaluation Reference: EVALUATION-A4-PHASE-2-003

---

## 1. Executive Summary

Antigravity has implemented the **Syft SBOM Generation Adapter** (`A4-SEC-001`), providing typed, local-only generation and verification of CycloneDX 1.5 JSON Software Bill of Materials (SBOM) evidence.

### Key Capabilities Implemented:
1. **Public Contracts (`SyftScanRequest` & `SyftScanResult`):**
   - Supports `source_kind: Literal["oci_image", "static_archive", "directory"]`.
   - Enforces preflight source confinement and cryptographic binding:
     - **OCI Images:** Enforces local registry confinement (`localhost:5100` or `127.0.0.1:5100`) and immutable pinning via `@sha256:<64-hex>`. Unpinned tags and remote registries are strictly rejected.
     - **Static Archives:** Pre-computes byte hash and size; asserts exact parity against `expected_source_digest` and `expected_source_size_bytes` before invoking Syft. Path traversal and symlinks are rejected.
     - **Directories:** Rejects symlink directory/file escapes; marks digest provenance as unverified unless a caller-supplied immutable `tree_hash` is present.
2. **Subprocess Execution & Argument Safety:**
   - Invokes Syft via argument vector (`[bin, target, "-o", "cyclonedx-json"]`) with bounded timeouts and `shell=False`.
   - Supports dependency injection (`runner` callable) for deterministic unit and offline testing.
3. **CycloneDX 1.5 JSON Document Validation:**
   - Validates UTF-8 encoding, JSON well-formedness, `bomFormat == "CycloneDX"`, `specVersion == "1.5"`, metadata, and component structure.
   - Computes authoritative raw-byte SHA-256 digest (`sha256:<hex>`).
4. **Supply Chain Reference Binding:**
   - Produces `ReleaseSupplyChainRef(format="CycloneDX-1.5-JSON", reference=..., sha256="sha256:<raw-byte hash>")` only when caller supplies an explicit, safe output path and persistence succeeds. In-memory scans omit references without publishing claims.
5. **Truthful Tooling Availability & Negative Testing:**
   - Tested host PATH for Syft (`where.exe syft` returned not found).
   - If the Syft CLI is missing and no runner is injected, the adapter returns an explicit `status="UNAVAILABLE"`, `verified=False` result with clear error messaging, never fabricating SBOM data.

---

## 2. Changed Files

Strictly confined to the authorized new files:
1. `platform_core/adapters/security/syft_adapter.py` (new adapter module)
   - Defines `SyftScanRequest`, `SyftScanResult`, `SyftAdapter`, and typed exceptions (`SyftUnavailableError`, `SyftValidationError`, `SyftExecutionError`, `SyftIntegrityError`, `SyftDocumentParsingError`).
2. `tests/unit/test_syft_adapter.py` (new unit test suite)
   - 19 isolated test cases covering positive OCI/static/directory scans, preflight rejections, execution failures, timeouts, malformed documents, version mismatches, and baseline preservation.
3. Protocol messages under `nero_devops_standard/codex2antigravity/02_antigravity_to_codex/`

*Note: `platform_core/adapters/security/__init__.py` was preserved untouched in accordance with task instructions.*

---

## 3. Sample CycloneDX 1.5 Output Metadata

```json
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.5",
  "serialNumber": "urn:uuid:3e671687-395b-41f5-a30f-a58921a69b79",
  "version": 1,
  "metadata": {
    "timestamp": "2026-11-15T12:00:00Z",
    "tools": [
      {
        "vendor": "anchore",
        "name": "syft",
        "version": "1.18.0"
      }
    ],
    "component": {
      "name": "hotel-billing-backend",
      "version": "1.0.0",
      "type": "container"
    }
  },
  "components": [
    {
      "name": "spring-boot-starter-web",
      "version": "3.1.2",
      "type": "library",
      "purl": "pkg:maven/org.springframework.boot/spring-boot-starter-web@3.1.2"
    },
    {
      "name": "jjwt-api",
      "version": "0.11.5",
      "type": "library",
      "purl": "pkg:maven/io.jsonwebtoken/jjwt-api@0.11.5"
    }
  ]
}
```

---

## 4. Test Verification & Evidence

### Isolated Test Execution: `tests.unit.test_syft_adapter`
```
test_01_valid_oci_image_scan (tests.unit.test_syft_adapter.TestSyftAdapter) ... ok
test_02_valid_static_archive_scan_with_persistence (tests.unit.test_syft_adapter.TestSyftAdapter) ... ok
test_03_valid_directory_scan_with_tree_hash (tests.unit.test_syft_adapter.TestSyftAdapter) ... ok
test_04_directory_scan_without_tree_hash_marks_provenance_unverified (tests.unit.test_syft_adapter.TestSyftAdapter) ... ok
test_05_unpinned_oci_image_rejected (tests.unit.test_syft_adapter.TestSyftAdapter) ... ok
test_06_nonlocal_oci_registry_rejected (tests.unit.test_syft_adapter.TestSyftAdapter) ... ok
test_07_oci_digest_mismatch_fails_closed (tests.unit.test_syft_adapter.TestSyftAdapter) ... ok
test_08_static_archive_digest_mismatch_fails_closed (tests.unit.test_syft_adapter.TestSyftAdapter) ... ok
test_09_static_archive_size_mismatch_fails_closed (tests.unit.test_syft_adapter.TestSyftAdapter) ... ok
test_10_missing_static_archive_file_fails_closed (tests.unit.test_syft_adapter.TestSyftAdapter) ... ok
test_11_missing_syft_returns_explicit_unavailable (tests.unit.test_syft_adapter.TestSyftAdapter) ... ok
test_12_subprocess_failure_fails_closed (tests.unit.test_syft_adapter.TestSyftAdapter) ... ok
test_13_subprocess_timeout_fails_closed (tests.unit.test_syft_adapter.TestSyftAdapter) ... ok
test_14_non_utf8_output_fails_closed (tests.unit.test_syft_adapter.TestSyftAdapter) ... ok
test_15_invalid_json_fails_closed (tests.unit.test_syft_adapter.TestSyftAdapter) ... ok
test_16_wrong_cyclonedx_spec_version_rejected (tests.unit.test_syft_adapter.TestSyftAdapter) ... ok
test_17_wrong_bom_format_rejected (tests.unit.test_syft_adapter.TestSyftAdapter) ... ok
test_18_malformed_component_data_rejected (tests.unit.test_syft_adapter.TestSyftAdapter) ... ok
test_19_stable_evidence_hash_reproducibility (tests.unit.test_syft_adapter.TestSyftAdapter) ... ok

----------------------------------------------------------------------
Ran 19 tests in 2.663s

OK
```

### Full 9-Suite Regression Test Execution:
```powershell
python -B -m unittest tests.unit.test_candidate_contract tests.unit.test_candidate_ingest tests.unit.test_release_manifest_v2 tests.unit.test_release_manifest tests.unit.test_registry_base tests.unit.test_oci_adapter tests.unit.test_s3_release_adapter tests.unit.test_distribution_dispatcher tests.unit.test_syft_adapter -q
```
**Results across all 9 suites:**
- Total tests: **193 passed, 0 failures, 0 errors in 18.285s**.

---

## 5. Authoritative Baselines & Governance Verification

| Baseline | Verified State | Status |
|---|---|---|
| **Audit Ledger Records** | 84 lines | **Unchanged** |
| **Audit Ledger SHA-256** | `77072d885be691c71a30514be97666a7937deb0aa87ac6f52f5490733c1ddf83` | **Strict Match** |
| **Terraform State** | Serial 23, 15 managed resources | **Unchanged** |
| **Cloud Spend** | $0.00 | **Zero spend** |
| **Git Repository** | 0 commits, 0 pushes | **Unchanged** |
| **Modified Files** | `platform_core/adapters/security/syft_adapter.py`<br>`tests/unit/test_syft_adapter.py` | **Strictly Confined** |

---

## 6. Live Tooling Readiness Assessment
- Host CLI Discovery: `where.exe syft` returned exit code 1 (not installed).
- Live qualification state: **PENDING_HOST_INSTALLATION**. The adapter correctly handles the absent binary by returning `status="UNAVAILABLE"` without fabricating mock data as live evidence.
- Status transition: `IMPLEMENTATION_COMPLETED`.
