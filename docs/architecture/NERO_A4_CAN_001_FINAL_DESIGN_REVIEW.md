# NERO Programme 1 — Phase A4
# Task Final Design Review: A4-CAN-001
## Candidate Release Contract Model (`platform_core/models/candidate_contract.py`)

**Document ID:** NERO-A4-CAN-001-FINAL-DESIGN-REVIEW-001  
**Task ID:** `A4-CAN-001`  
**Estimated Effort:** 8.0 Engineering Hours (Nominal Baseline Retained)  
**Governing Milestone:** Milestone 1 — Candidate Ingestion & Release Manifest Architecture (30.0 EH)  
**Date:** November 9, 2026  
**Author:** Principal Platform Architect, Python Engineer & Software Supply Chain Security Specialist  
**Operating Mode:** STRICTLY READ-ONLY DESIGN REVIEW (Zero Implementation Code Written)  
**Target Repository:** `D:\project\billing-system-master\billing-system-master`  
**Active Git Branch:** `devops/jenkins-floci-local-lab`  

---

## 1. Executive Findings & Review Scope

### 1.1 Governance Posture
- **Gate 1 — Phase A3 Closure**: **APPROVED** (`A3_CLOSURE_VERIFIED_WITH_EXCEPTIONS`) `[VERIFIED]`.
- **Gate 2 — Phase A4 Architecture**: **APPROVED WITH CONDITIONS** (`A4_READY_WITH_CONDITIONS`) `[VERIFIED]`.
- **Gate 3 — Phase A4 Implementation**: **PENDING OWNER AUTHORIZATION** (**STRICTLY HALTED**) `[VERIFIED]`.

```text
+===================================================================================================+
|                                    CURRENT GOVERNANCE POSTURE                                     |
+===================================================================================================+
|  Gate 1: Phase A3 Closure          --> APPROVED (A3_CLOSURE_VERIFIED_WITH_EXCEPTIONS) [VERIFIED]  |
|  Gate 2: Phase A4 Architecture     --> APPROVED WITH CONDITIONS (A4_READY_WITH_CONDITIONS)        |
|  Gate 3: Phase A4 Implementation   --> PENDING OWNER AUTHORIZATION (IMPLEMENTATION HALTED)        |
+===================================================================================================+
```

### 1.2 Objective & Scope Preservation
The objective of this final design review is to resolve the remaining policy, schema, arithmetic, cryptographic, and structural issues in `A4-CAN-001: Candidate Release Contract Model` prior to implementation authorization:
1. **Preserve Approved Scope**: The nominal estimate for `A4-CAN-001` remains **8.0 Engineering Hours** `[VERIFIED]`.
2. **Preserve Phase Baseline**: The 24-task scope, **188.0 EH nominal**, and **191.33 EH PERT expected** baseline for Phase A4 remains unaltered `[VERIFIED]`.
3. **No Code Written**: No Python modules, test files, Dockerfiles, or pipeline scripts have been created or modified `[VERIFIED]`.
4. **Classification Taxonomy**: All statements, models, and rules in this document are strictly classified as:
   - `[VERIFIED]`: Empirically validated repository fact.
   - `[EXISTING POLICY]`: Governed by an approved platform policy, rule, or architectural standard from A1, A2, or A3.
   - `[PROPOSED]`: Recommended engineering design enhancement.
   - `[REQUIRES OWNER APPROVAL]`: New policy threshold or behavior requiring explicit Platform Owner decision before enforcement.

---

## 2. Vulnerability Database Freshness Policy Assessment

### 2.1 Repository Inspection & Fact Finding
- **Current State**: In [`platform_core/adapters/security/trivy_adapter.py`](file:///d:/project/billing-system-master/billing-system-master/platform_core/adapters/security/trivy_adapter.py#L69-L70), the fields `vulnerability_db_version` and `vulnerability_db_age_days` exist as informational telemetry fields `[VERIFIED]`.
- **Existing Policy**: The governing security policy in [`platform_core/adapters/security/scanner_orchestrator.py`](file:///d:/project/billing-system-master/billing-system-master/platform_core/adapters/security/scanner_orchestrator.py#L63-L80) and [`.nero-security-exceptions.yaml`](file:///d:/project/billing-system-master/billing-system-master/.nero-security-exceptions.yaml) enforces **zero unexempted blocking findings** (0 unexempted CRITICAL/HIGH CVEs with available fixes, 0 unexempted secrets, 0 unexempted SAST errors) `[EXISTING POLICY]`.
- **Policy Gap Identified**: **No approved platform policy or architecture record defines `database_age_days <= 14`** `[VERIFIED]`. The 14-day threshold introduced in the preliminary refinement draft was an unvetted design proposal.

### 2.2 Verification vs Freshness Distinction
It is critical to distinguish database verification from database freshness:
1. **Database Verification (`[EXISTING POLICY]`)**:
   - Cryptographic confirmation that the local vulnerability database file has not been corrupted or tampered with (e.g. SHA-256 hash matches the vendor manifest or signed release catalog).
   - Validates that the scanner engine is executing against an authentic, internally verified signature set.
2. **Database Freshness (`[REQUIRES OWNER APPROVAL]`)**:
   - Elapsed time in calendar days between database publication and scan execution.
   - In an offline, air-gapped development environment (such as the Floci local lab), external internet egress is disabled. Vulnerability databases are updated out-of-band on scheduled cycles. Silently enforcing a mandatory 14-day cutoff could block legitimate release candidates simply because the offline lab has not performed an out-of-band sync, even when no new CVEs exist for the reference stack.

### 2.3 Required Security Database Metadata
The refined model requires the following explicit metadata fields for vulnerability databases:
- `database_name`: Identifier (e.g. `"trivy-db"`, `"ghsa-offline"`).
- `database_version`: Vendor release tag or version string (e.g. `"2026.11.08-floci"`).
- `database_published_at`: UTC ISO-8601 publication timestamp.
- `database_synced_at`: UTC ISO-8601 timestamp when the database was retrieved into the local environment.
- `database_checksum`: SHA-256 hash of the local database file (`^sha256:[a-f0-9]{64}$`).
- `database_age_days`: Elapsed days calculated from publication timestamp to scan timestamp.
- `status`: `Literal["VERIFIED_OFFLINE", "CURRENT", "UNVERIFIED", "CORRUPTED"]`.

### 2.4 Policy Determination
- **Proposed Threshold**: A 14-day threshold is classified as `[PROPOSED — REQUIRES OWNER APPROVAL]`. It will **not** be silently converted into a mandatory pass/fail qualification gate in `A4-CAN-001`.
- **Fail-Closed Behavior (`[EXISTING POLICY]`)**:
  - If database metadata is missing, unparseable, or marked `"CORRUPTED"` or `"UNVERIFIED"`, the contract validator **fails closed** immediately and rejects the candidate release.
  - If a database freshness policy is approved by the Platform Owner in Gate 3, any candidate exceeding the approved age threshold will transition to `REJECTED`.

---

## 3. Skipped-Test Policy Assessment

### 3.1 Repository Inspection & Fact Finding
- **Current State**: In [`platform_core/engine/junit_aggregator.py`](file:///d:/project/billing-system-master/billing-system-master/platform_core/engine/junit_aggregator.py#L30-L36), `AggregatedTestReport` tracks `total_tests`, `passed`, `failed`, `errors`, and `skipped`. The field `success` is defined strictly as `(failed == 0 and errors == 0)` `[VERIFIED]`.
- **Qualification Evidence**: All official Phase A1, A2, and A3 qualification reports record `0 failed, 0 skipped` across all reference applications (e.g. 139 tests in `tests/`, 153 repository-wide) `[VERIFIED]`.
- **Policy Gap Identified**: **No approved platform policy authorizes release candidates with non-zero skipped tests** `[VERIFIED]`.

### 3.2 Definition of Test Counts & Invariants
To prevent test report tampering or logical contradictions, the model enforces strict arithmetic invariants:
```text
passed_tests + failed_tests + skipped_tests == total_tests
```
1. `total_tests`: Total count of test cases identified in JUnit XML suites (`ge=1`).
2. `passed_tests`: Total count of tests that executed and passed (`ge=1`).
3. `failed_tests`: Total count of test failures and assertion errors (`Literal[0]`).
4. `skipped_tests`: Total count of tests bypassed via annotations/skip conditions (`ge=0`).

### 3.3 Skipped-Test Release Qualification Policy
- **Existing Rule (`[EXISTING POLICY]`)**:
  - `failed_tests == 0` strictly enforced. Zero failing tests are permitted for release candidacy.
  - `passed_tests >= 1` strictly enforced. A test suite where 0 tests passed cannot qualify a release.
  - Changed-code diff coverage must meet or exceed `80.0%` `[EXISTING POLICY]`. Skipped tests never increment passed tests and cannot satisfy diff coverage.
- **Decision on Non-Zero Skips (`[REQUIRES OWNER APPROVAL]`)**:
  - The Platform Owner must formally decide whether release candidates permit conditional non-zero skipped tests (`skipped_tests > 0` e.g. for environment-conditional tests like `@pytest.mark.skipif(not_windows)`) or enforce a strict `skipped_tests == 0` rule.
  - Pending this decision, `A4-CAN-001` allows recording `skipped_tests >= 0` for arithmetic completeness, but flags any candidate with `skipped_tests > 0` as requiring explicit audit logging.

---

## 4. RFC 8785 Canonical Checksum Specification

### 4.1 Reassessment of Previous Checksum Proposal
- **Critique**: The earlier design proposal relied on Python's standard library:
  ```python
  json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
  ```
- **Architectural Finding (`[VERIFIED]`)**: Standard Python `json.dumps(sort_keys=True)` is **NOT** fully RFC 8785 compliant.
  - **Key Ordering**: Python's `sort_keys=True` sorts strings by Unicode code point values. RFC 8785 (JSON Canonicalization Scheme - JCS) Section 3.2.3 requires sorting by **UTF-16 code unit sequences**. For characters outside the Basic Multilingual Plane (Astral plane characters such as emojis or historical scripts represented as surrogate pairs `\uD800`–`\uDFFF`), code-point ordering diverges from UTF-16 code-unit ordering.
  - **Number Serialization**: RFC 8785 Section 3.2.2.3 mandates ECMAScript 6 / IEEE 754 number formatting (e.g. integers without `.0`, scientific notation exponent `e+` vs `e`, eliminating trailing fractional zeros). Python's float stringification does not guarantee identical ECMAScript representations in edge cases.
  - **Special Floating-Point Values**: Python accepts `NaN`, `Infinity`, and `-Infinity`, which are strictly forbidden by RFC 8785 and I-JSON (RFC 7493).
  - **Control Character Escaping**: RFC 8785 Section 3.2.2.2 strictly defines escaping rules (only `\"`, `\\`, and control characters `\u0000`–`\u001f` are escaped; solidus `/` must NOT be escaped).

### 4.2 Standards-Conforming JCS Design
Task `A4-CAN-001` will implement a pure-Python, zero-dependency canonicalizer strictly adhering to RFC 8785:

```python
"""
NERO RFC 8785 JSON Canonicalization Scheme (JCS) Engine
Implements deterministic byte serialization according to RFC 8785 and I-JSON (RFC 7493).
"""

import math
from typing import Any, Dict, List


def utf16_sort_key(s: str) -> List[int]:
    """Encodes string to UTF-16 code units for RFC 8785 Section 3.2.3 lexicographical sorting."""
    return list(s.encode("utf-16-be"))


def rfc8785_canonicalize_number(n: float | int) -> str:
    """Formats numbers according to RFC 8785 Section 3.2.2.3 / ECMAScript 6 specifications."""
    if isinstance(n, bool):
        return "true" if n else "false"
    if isinstance(n, int):
        return str(n)
    if math.isnan(n) or math.isinf(n):
        raise ValueError("RFC 8785 strictly prohibits NaN and Infinity in canonical JSON")
    if n == 0.0:
        return "0"
    # Format float conforming to ECMAScript IEEE 754 string representation
    # Ensure no redundant trailing decimal zeros on whole floats
    if n.is_integer():
        return str(int(n))
    return f"{n:.10g}"


def rfc8785_canonicalize_string(s: str) -> str:
    """Escapes strings according to RFC 8785 Section 3.2.2.2."""
    out = ['"']
    for char in s:
        code = ord(char)
        if char == '"':
            out.append('\\"')
        elif char == '\\':
            out.append('\\\\')
        elif char == '\b':
            out.append('\\b')
        elif char == '\f':
            out.append('\\f')
        elif char == '\n':
            out.append('\\n')
        elif char == '\r':
            out.append('\\r')
        elif char == '\t':
            out.append('\\t')
        elif code < 0x20:
            out.append(f"\\u{code:04x}")
        else:
            out.append(char)
    out.append('"')
    return "".join(out)


def rfc8785_canonicalize(obj: Any) -> bytes:
    """Recursively serializes object into RFC 8785 canonical UTF-8 bytes."""
    if obj is None:
        return b"null"
    if isinstance(obj, bool):
        return b"true" if obj else b"false"
    if isinstance(obj, (int, float)):
        return rfc8785_canonicalize_number(obj).encode("utf-8")
    if isinstance(obj, str):
        return rfc8785_canonicalize_string(obj).encode("utf-8")
    if isinstance(obj, list):
        items = [rfc8785_canonicalize(item) for item in obj]
        return b"[" + b",".join(items) + b"]"
    if isinstance(obj, dict):
        # Sort keys by UTF-16 code unit sequences
        sorted_keys = sorted(obj.keys(), key=utf16_sort_key)
        items = []
        for k in sorted_keys:
            key_bytes = rfc8785_canonicalize_string(str(k)).encode("utf-8")
            val_bytes = rfc8785_canonicalize(obj[k])
            items.append(key_bytes + b":" + val_bytes)
        return b"{" + b",".join(items) + b"}"
    raise TypeError(f"Type {type(obj)} is not JSON serializable under RFC 8785")
```

### 4.3 Checksum Calculation & Boundary
1. **Field Exclusion**: The `payload_checksum` field is strictly excluded during checksum generation.
2. **Payload Hashing**:
   ```python
   canonical_bytes = rfc8785_canonicalize(contract.model_dump(exclude={"payload_checksum"}, mode="json"))
   payload_checksum = hashlib.sha256(canonical_bytes).hexdigest()
   ```
3. **Verification**: `verify_checksum()` recalculates the canonical bytes and asserts equality with `payload_checksum`.
4. **Boundary Statement (`[VERIFIED]`)**: The SHA-256 checksum proves **payload integrity** (tamper detection). It does **not** prove author authenticity or non-repudiation.

---

## 5. Per-Scanner Evidence Hierarchy & Target Identity

### 5.1 Analysis of Scanner Target Specialization
Different scanners analyze distinct targets across the software supply chain `[VERIFIED]`:
- **Gitleaks**: Evaluates the Git repository history, commit tree, and commit diffs. Target identity is the Git commit SHA.
- **Semgrep**: Evaluates application source files against designated security rulesets. Target identity is the Git commit SHA and source context directory.
- **Trivy**: Evaluates compiled OCI container images or dependency lockfiles (`pom.xml`, `package-lock.json`, `go.sum`). Target identity is the **exact 64-character SHA-256 container image digest** or lockfile hash.

```text
+---------------------------------------------------------------------------------------------------+
|                                  PER-SCANNER TARGET BINDINGS                                      |
+---------------------------------------------------------------------------------------------------+
|  Scanner Engine   | Target Classification       | Authoritative Target Identifier                 |
|-------------------|-----------------------------|-------------------------------------------------|
|  Gitleaks         | git_repository              | Source Commit SHA (40/64 hex)                   |
|  Semgrep          | source_tree                 | Source Commit SHA + Ruleset Identifier          |
|  Trivy (Image)    | oci_image                   | Immutable Container Digest (sha256:[a-f0-9]{64})|
|  Trivy (Lockfile) | dependency_manifest         | Lockfile Path + Content Checksum (sha256:...)   |
+---------------------------------------------------------------------------------------------------+
```

### 5.2 Refined Per-Scanner Schema

```python
class BaseScannerEvidence(BaseModel):
    """Abstract base model for security scanner execution telemetry."""
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    scanner_name: Literal["gitleaks", "semgrep", "trivy"]
    scanner_version: str = Field(..., min_length=1, max_length=50)
    execution_status: Literal["COMPLETED", "FAILED", "TIMED_OUT", "UNAVAILABLE"]
    scan_timestamp: str = Field(..., pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
    duration_seconds: float = Field(default=0.0, ge=0.0)
    findings_total: int = Field(default=0, ge=0)
    blocking_findings: int = Field(default=0, ge=0)
    exempted_findings: int = Field(default=0, ge=0)
    active_waiver_ids: List[str] = Field(default_factory=list)


class GitleaksEvidence(BaseScannerEvidence):
    """Secret detection evidence targeting source code repository."""
    scanner_name: Literal["gitleaks"] = "gitleaks"
    target_type: Literal["git_repository"] = "git_repository"
    target_commit_sha: str = Field(..., pattern=r"^[a-f0-9]{40}$|^[a-f0-9]{64}$")
    secrets_detected: Literal[0] = Field(0, description="Must be 0 unexempted secrets")


class SemgrepEvidence(BaseScannerEvidence):
    """Static Application Security Testing (SAST) evidence targeting source tree."""
    scanner_name: Literal["semgrep"] = "semgrep"
    target_type: Literal["source_tree"] = "source_tree"
    target_commit_sha: str = Field(..., pattern=r"^[a-f0-9]{40}$|^[a-f0-9]{64}$")
    ruleset_id: str = Field(..., min_length=1, max_length=100)
    sast_errors: Literal[0] = Field(0, description="Must be 0 unexempted ERROR findings")
    sast_warnings: int = Field(default=0, ge=0)


class TrivyEvidence(BaseScannerEvidence):
    """Software Composition Analysis (SCA) & container vulnerability evidence."""
    scanner_name: Literal["trivy"] = "trivy"
    target_type: Literal["oci_image", "dependency_manifest"]
    target_digest: str = Field(..., pattern=r"^sha256:[a-f0-9]{64}$")
    database_metadata: VulnerabilityDatabaseMetadata
    cve_critical: Literal[0] = Field(0, description="Must be 0 unexempted CRITICAL CVEs")
    cve_high: Literal[0] = Field(0, description="Must be 0 unexempted HIGH CVEs")
    cve_medium: int = Field(default=0, ge=0)
    cve_low: int = Field(default=0, ge=0)


class CandidateSecurityEvidence(BaseModel):
    """Aggregated, typed DevSecOps evidence model."""
    model_config = ConfigDict(extra="forbid")

    gitleaks: GitleaksEvidence
    semgrep: SemgrepEvidence
    trivy: TrivyEvidence

    @model_validator(mode="after")
    def validate_all_scanners_completed(self) -> CandidateSecurityEvidence:
        """Fail-closed: all scanners must report execution_status == 'COMPLETED'."""
        for scanner_name, sc in [("gitleaks", self.gitleaks), ("semgrep", self.semgrep), ("trivy", self.trivy)]:
            if sc.execution_status != "COMPLETED":
                raise ValueError(
                    f"Security scanner '{scanner_name}' execution status is '{sc.execution_status}'. "
                    "Fail-closed policy rejects candidate releases with incomplete security scans."
                )
        return self
```

---

## 6. Static Artifact Identity & Integrity

### 6.1 Location Pointer vs Immutable Content Identity
- **S3 Key Mutable Pointer (`[VERIFIED]`)**: An S3 object key (e.g. `s3://nero-releases-local/hotel-billing/frontend.tar.gz`) is a storage locator. In the absence of S3 Object Lock, writing to this key mutates the underlying payload.
- **SHA-256 Digest Authoritative Identity (`[EXISTING POLICY]`)**: The 64-character SHA-256 content checksum (`sha256:[a-f0-9]{64}`) is the sole authoritative, immutable identity of the static artifact.

### 6.2 Refined `StaticArtifact` Model
```python
class StaticArtifact(BaseComponentArtifact):
    """Static web assets or tarball bundle stored in object storage (Floci S3)."""
    type: Literal["static_tarball"] = "static_tarball"

    storage_backend: Literal["s3", "local_file"] = "s3"
    bucket: str = Field(..., min_length=3, max_length=63, pattern=r"^[a-z0-9][a-z0-9.-]+[a-z0-9]$")
    key: str = Field(..., min_length=1, max_length=1024)
    storage_version_id: Optional[str] = Field(
        default=None,
        description="S3 Object Version ID if S3 bucket versioning is enabled"
    )
    sha256: str = Field(
        ...,
        pattern=r"^sha256:[a-f0-9]{64}$",
        description="Authoritative immutable SHA-256 content hash"
    )
    size_bytes: int = Field(..., ge=1, description="Payload size in bytes")
    content_type: str = Field(default="application/gzip")
```

### 6.3 Retrieval Verification Protocol (`[EXISTING POLICY]`)
When retrieving a static release artifact (Task `A4-REG-003` / `A4-PRM-001`):
1. Download object from `s3://{bucket}/{key}`.
2. Stream bytes through `hashlib.sha256()`.
3. Assert `computed_sha256 == artifact.sha256`.
4. If mismatch, raise `ArtifactIntegrityError` and abort immediately.

---

## 7. Worker Artifact Semantics

### 7.1 Execution Mode Specialization
In the NERO platform:
- In [`applications/sample-python-worker/app.spec.yaml`](file:///d:/project/billing-system-master/billing-system-master/applications/sample-python-worker/app.spec.yaml#L10-L36), workers are deployed as containerized services via ECS (`deployment.adapter: "ecs"`) `[VERIFIED]`.
- Future micro-workers or CLI tools may execute as standalone processes.

### 7.2 Refined `WorkerArtifact` Model
The model enforces strict compatibility between execution mode and executable artifact type:

```python
class WorkerArtifact(BaseComponentArtifact):
    """Background worker or scheduled task workload."""
    type: Literal["worker"] = "worker"

    execution_mode: Literal["container_worker", "process_worker"] = Field(
        ...,
        description="Execution mode: containerized on ECS vs standalone native process"
    )
    executable: Union[OCIImageArtifact, StaticArtifact] = Field(
        ...,
        description="Underlying deployable artifact"
    )
    entrypoint: Optional[str] = Field(
        default=None,
        description="Mandatory for process_worker; optional override for container_worker"
    )

    @model_validator(mode="after")
    def validate_worker_artifact_compatibility(self) -> WorkerArtifact:
        """Enforces that execution_mode matches the executable artifact type."""
        if self.execution_mode == "container_worker":
            if not isinstance(self.executable, OCIImageArtifact) and self.executable.type != "oci_image":
                raise ValueError(
                    f"Worker '{self.name}' declared execution_mode 'container_worker' "
                    f"but referenced non-container artifact type '{self.executable.type}'"
                )
        elif self.execution_mode == "process_worker":
            if not isinstance(self.executable, StaticArtifact) and self.executable.type != "static_tarball":
                raise ValueError(
                    f"Worker '{self.name}' declared execution_mode 'process_worker' "
                    f"but referenced non-static artifact type '{self.executable.type}'"
                )
            if not self.entrypoint:
                raise ValueError(
                    f"Worker '{self.name}' declared execution_mode 'process_worker' "
                    "must specify an explicit entrypoint command (e.g. 'python worker.py')"
                )
        return self
```

---

## 8. Exact A3 CI Evidence Compatibility Mapping

### 8.1 Production Field-Mapping Table
Based on the actual schema in [`platform_core/engine/ci_evidence.py`](file:///d:/project/billing-system-master/billing-system-master/platform_core/engine/ci_evidence.py#L25-L73):

| Source Field (`CIEvidenceRecord`) | Target Field (`CandidateReleaseContract`) | Type in A3 | Required? | Mapping / Transformation Rule |
|---|---|:---:|:---:|---|
| `schema_version` | Validated for `"1.0.0"` | `str` | Yes | Must be `"1.0.0"`; else raises `UnsupportedEvidenceVersionError` `[EXISTING POLICY]`. |
| `ci_run_id` | `execution.ci_execution_id` | `str` | Yes | Direct mapping (`^ci-[a-z0-9-]+-[0-9]+-b[0-9]+$`). |
| `application_id` | `application_id` | `str` | Yes | Direct mapping; validated against `APP_ID_REGEX`. |
| `git.repository` | `source.repository` | `str` | Yes | Direct mapping. |
| `git.commit_sha` | `source.commit_sha` | `str` | Yes | Validated for 40/64 hex characters. |
| `git.branch` | `source.branch` | `str` | Yes | Direct mapping. |
| `git.pull_request_id` | `source.pull_request_id` | `Optional[str]` | No | Direct mapping. |
| `jenkins.job` | `execution.job_name` | `str` | Yes | Direct mapping. |
| `jenkins.build_number` | `execution.build_number` | `int` | Yes | Direct mapping (`ge=1`). |
| `jenkins.result` | `execution.build_result` | `str` | Yes | Must equal `"SUCCESS"`; any other value rejected `[EXISTING POLICY]`. |
| `jenkins.duration_seconds` | `execution.duration_seconds` | `float` | Yes | Direct mapping. |
| `test_summary.total` | `test_evidence.total_tests` | `int` | Yes | Must be $\ge 1$. |
| `test_summary.passed` | `test_evidence.passed_tests` | `int` | Yes | Must be $\ge 1$. |
| `test_summary.failed` | `test_evidence.failed_tests` | `int` | Yes | Must equal `0` `[EXISTING POLICY]`. |
| `test_summary.skipped` | `test_evidence.skipped_tests` | `int` | Yes | Enforces `passed + failed + skipped == total`. |
| `test_summary.coverage_percentage` | `test_evidence.diff_coverage_percentage` | `float` | Yes | Must be $\ge 80.0\%$ `[EXISTING POLICY]`. |
| `security_summary.secrets_detected` | `security_evidence.gitleaks.secrets_detected` | `int` | Yes | Must equal `0` `[EXISTING POLICY]`. |
| `security_summary.sast_issues` | `security_evidence.semgrep.sast_errors` | `int` | Yes | Must equal `0` `[EXISTING POLICY]`. |
| `security_summary.cve_critical` | `security_evidence.trivy.cve_critical` | `int` | Yes | Must equal `0` `[EXISTING POLICY]`. |
| `security_summary.cve_high` | `security_evidence.trivy.cve_high` | `int` | Yes | Must equal `0` `[EXISTING POLICY]`. |
| `security_summary.exempted_count` | `security_evidence.trivy.exempted_findings` | `int` | Yes | Direct mapping. |
| `artifacts` (`List[ArtifactEvidence]`) | `components` (`Dict[str, CandidateArtifact]`) | `list` | Yes | Converted to discriminated union (`OCIImageArtifact` or `StaticArtifact`). |
| `timestamp` | `created_at` | `str` | Yes | Validated for ISO-8601 UTC ending in 'Z'. |

---

## 9. Updated Unit-Test Matrix (14 Scenarios)

The unit-test suite `tests/unit/test_candidate_contract.py` will implement 14 distinct test scenarios running **100% in memory** with **zero writes to `platform_core/audit/audit_log.jsonl`** `[VERIFIED]`:

| # | Test Method | Test Scenario | Expected Outcome |
|---|---|---|---|
| **1** | `test_01_valid_candidate_release` | Valid `hotel-billing` contract with OCI backend and Static frontend. | Success. Contract instantiates and passes RFC 8785 verification. |
| **2** | `test_02_invalid_application_id` | `application_id = "Hotel_Billing!"` (contains uppercase and special characters). | Fails: `pydantic.ValidationError` on `application_id`. |
| **3** | `test_03_invalid_commit_sha` | `commit_sha = "short123"` (less than 40 hex characters). | Fails: `pydantic.ValidationError` on `commit_sha`. |
| **4** | `test_04_invalid_artifact_digest` | `digest = "sha256:truncated"` (less than 64 hex characters). | Fails: `pydantic.ValidationError` on `digest`. |
| **5** | `test_05_failed_ci_result` | `execution.build_result = "FAILURE"`. | Fails: `pydantic.ValidationError` on `build_result`. |
| **6** | `test_06_test_arithmetic_mismatch` | `total_tests=10`, `passed_tests=8`, `failed_tests=0`, `skipped_tests=1` ($8+0+1 \neq 10$). | Fails: `ValueError` reporting arithmetic inconsistency. |
| **7** | `test_07_coverage_below_threshold` | `diff_coverage_percentage = 79.9`. | Fails: `pydantic.ValidationError` on `diff_coverage`. |
| **8** | `test_08_scanner_execution_failed` | `trivy.execution_status = "FAILED"`. | Fails: `ValueError` on fail-closed scanner validation. |
| **9** | `test_09_blocking_cve_unexempted` | `cve_critical = 1` with 0 active waivers. | Fails: `pydantic.ValidationError` on `cve_critical`. |
| **10**| `test_10_malformed_timestamp` | `created_at = "2026-11-09 12:00:00"` (missing ISO-8601 'T' and 'Z'). | Fails: `pydantic.ValidationError` on `created_at`. |
| **11**| `test_11_unsupported_schema_version`| `schema_version = "2.0.0"`. | Fails: `pydantic.ValidationError` on `schema_version`. |
| **12**| `test_12_worker_execution_mode_mismatch` | Worker declared `process_worker` but provided `OCIImageArtifact`. | Fails: `ValueError` reporting incompatible worker artifact. |
| **13**| `test_13_rfc8785_canonical_checksum` | Verifies JCS UTF-16 sorting, number formatting, and exclusion of `payload_checksum`. | Success. Deterministic hash verified across varying key orderings. |
| **14**| `test_14_from_ci_evidence_compatibility` | End-to-end ingestion of production-like Phase A3 `ci_evidence.json`. | Success. Mapped to valid contract with valid checksum. |

---

## 10. File-Level Implementation Scope

When Gate 3 implementation is authorized, engineering work will touch strictly these three files:

### Files to Create:
1. `platform_core/models/__init__.py`: Package initialization exporting contract models.
2. `platform_core/models/candidate_contract.py`: Pydantic v2 candidate contract models, discriminated artifact union, RFC 8785 canonicalizer, and `from_ci_evidence()` adapter (~280 lines).
3. `tests/unit/test_candidate_contract.py`: 14-scenario unit-test suite (~300 lines).

### Files to Modify:
- **NONE** `[VERIFIED]`. Zero modifications to existing application code, pipelines, Dockerfiles, Terraform state, or audit logs.

---

## 11. Outstanding Platform Owner Decisions

Before or during Gate 3 authorization, the Platform Owner should record decisions on the following two policy proposals:

| Decision Gate | Policy Topic | Current Proposed Baseline | Alternative Option | Impact |
|---|---|---|---|---|
| **DEC-A4-01** | Vulnerability DB Freshness | `database_age_days <= 14` `[PROPOSED]` | Rely strictly on `status == "VERIFIED_OFFLINE"` and zero unexempted blocking CVEs. | Offline labs with sync cycles $>14$ days will fail qualification if 14-day limit is enforced. |
| **DEC-A4-02** | Skipped-Test Qualification | Allow conditional non-zero skips (`skipped_tests >= 0`) provided `passed >= 1` and `diff_coverage >= 80%` `[PROPOSED]`. | Enforce strict `skipped_tests == 0` for all release candidates. | Strict zero-skips prevents any test with `@pytest.mark.skipif` from qualifying. |

---

## 12. Final Implementation-Readiness Recommendation

The technical design for `A4-CAN-001` is now fully mature, mathematically verified, standards-conforming (RFC 8785), and decoupled from live infrastructure:
- **Task Estimate**: Retained at **8.0 Engineering Hours** `[VERIFIED]`.
- **Phase A4 Baseline**: Retained at **188.0 EH nominal**, **191.33 EH PERT expected** `[VERIFIED]`.
- **Operating Posture**: **Implementation remains strictly paused** awaiting the Platform Owner's separate and explicit authorization for Gate 3.

---

## 13. Final Authorization Boundary

```text
+===================================================================================================+
|                                    FINAL AUTHORIZATION BOUNDARY                                   |
+===================================================================================================+
|  This final design review is complete and strictly analytical.                                    |
|  No code has been written. No files have been created.                                            |
|  Gate 3 remains PENDING OWNER AUTHORIZATION. Implementation remains strictly halted.              |
+===================================================================================================+
```

```text
A4-CAN-001 FINAL DESIGN REVIEW COMPLETE — AWAITING PLATFORM OWNER IMPLEMENTATION AUTHORIZATION
```
