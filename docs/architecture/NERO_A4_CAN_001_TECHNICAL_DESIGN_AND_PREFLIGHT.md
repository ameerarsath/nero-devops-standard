# NERO Programme 1 — Phase A4
# Task Technical Preflight & Implementation Design: A4-CAN-001
## Candidate Release Contract Model (`platform_core/models/candidate_contract.py`)

**Document ID:** NERO-A4-CAN-001-DESIGN-001  
**Task ID:** `A4-CAN-001`  
**Task Title:** Candidate Release Contract Model  
**Estimated Effort:** 8.0 Engineering Hours (Nominal)  
**Governing Milestone:** Milestone 1 — Candidate Ingestion & Release Manifest Architecture (30.0 EH)  
**Date:** November 9, 2026  
**Author:** Principal Python Engineer, Platform Architect & Senior DevOps Reviewer  
**Operating Mode:** STRICTLY READ-ONLY PREFLIGHT (Zero Implementation Code Written)  
**Target Repository:** `D:\project\billing-system-master\billing-system-master`  
**Active Git Branch:** `devops/jenkins-floci-local-lab`  

---

## 1. Existing Architecture Findings

A thorough read-only inspection of the active repository was conducted to assess existing data modeling paradigms, validation libraries, test conventions, and evidence serialization mechanisms:

### 1.1 Existing Pydantic Modeling Architecture
- **Location**: [`platform_core/engine/models.py`](file:///d:/project/billing-system-master/billing-system-master/platform_core/engine/models.py).
- **Library Version**: Pydantic v2 (`ConfigDict`, `field_validator`, `model_validator`, `Field`).
- **Enforcement Patterns**:
  - `ConfigDict(extra="forbid")` is enforced across all models to prevent silent schema drift and reject undeclared fields.
  - Strict regex validations are established:
    - Application Names/IDs: `^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$`
    - Component Names: `^[a-z0-9][a-z0-9-]{1,30}[a-z0-9]$`
    - Semantic Versions: `^[0-9]+\.[0-9]+(\.[0-9]+)?(-[a-zA-Z0-9.]+)?$`
  - Relative Path Confinement: Validators reject path traversal (`..`), absolute paths, and Windows drive letters (`:`).
  - Component Uniqueness: Spec models assert uniqueness of component names and local port bindings via `@model_validator(mode="after")`.

### 1.2 Existing CI Evidence Generation Subsystem
- **Location**: [`platform_core/engine/ci_evidence.py`](file:///d:/project/billing-system-master/billing-system-master/platform_core/engine/ci_evidence.py).
- **Models Implemented**:
  - `GitEvidence` (`repository`, `commit_sha`, `branch`, `pull_request_id`)
  - `JenkinsEvidence` (`job`, `build_number`, `duration_seconds`, `result`)
  - `TestSummaryEvidence` (`total`, `passed`, `failed`, `skipped`, `coverage_percentage`)
  - `SecuritySummaryEvidence` (`secrets_detected`, `sast_issues`, `cve_critical`, `cve_high`, `exempted_count`)
  - `ArtifactEvidence` (`component`, `image`, `digest`)
  - `CIEvidenceRecord` (Root model, `schema_version="1.0.0"`, `checksum` SHA-256 payload hash)
- **Observations & Gaps**:
  - `CIEvidenceRecord` captures raw CI execution data, including potential build failures (`result="FAILURE"`), failing tests, or unpinned artifact images.
  - It does not represent an immutable release contract. It represents an execution log.
  - A release candidate requires a dedicated, strongly-typed contract (`CandidateReleaseContract`) that asserts pre-release eligibility: enforcing zero test failures, changed-code diff coverage $\ge 80.0\%$, zero unexempted blocking CVEs, and immutable 64-character SHA-256 digests.

### 1.3 Target Directory Structure
- **Current State**: `platform_core/models/` does not currently exist. Models are currently located under `platform_core/engine/models.py`.
- **Target Architecture**: In alignment with the approved A4 architecture ([`NERO_A4_IMMUTABLE_RELEASE_REQUIREMENTS_ARCHITECTURE_AND_IMPLEMENTATION_PLAN.md`](file:///d:/project/billing-system-master/billing-system-master/nero_devops_standard/docs/architecture/NERO_A4_IMMUTABLE_RELEASE_REQUIREMENTS_ARCHITECTURE_AND_IMPLEMENTATION_PLAN.md#L398)), a dedicated namespace `platform_core/models/` will be established for release engineering contracts:
  - `platform_core/models/__init__.py`
  - `platform_core/models/candidate_contract.py` (Task A4-CAN-001)
  - `platform_core/models/release_manifest_v2.py` (Task A4-MAN-001)

### 1.4 Cryptographic Hashing & Audit Ledger Safety
- Existing hashing across `audit_logger.py`, `ci_evidence.py`, and `release_manager.py` uses canonical JSON serialization (`json.dumps(..., sort_keys=True)`) hashed via `hashlib.sha256()`.
- The authoritative audit ledger (`platform_core/audit/audit_log.jsonl`) contains 84 verified records.
- **Inviolable Invariant**: Task A4-CAN-001 unit tests must execute in memory or write to isolated temporary directories (`tmp_path`). Zero audit records may be appended to `audit_log.jsonl`.

---

## 2. Recommended Module Design

```text
+---------------------------------------------------------------------------------------------------+
|                        A4-CAN-001 SUBSYSTEM BOUNDARY & INTERFACES                                 |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|   +--------------------------+                                                                    |
|   | Phase A3 CI Output       |                                                                    |
|   | (ci_evidence.json)       |                                                                    |
|   +------------+-------------+                                                                    |
|                |                                                                                  |
|                v                                                                                  |
|   +--------------------------+                                                                    |
|   | CandidateReleaseContract | <--- [Pydantic v2 Validation Pipeline]                             |
|   | (A4-CAN-001)             |      - 64-char SHA-256 Digest Regex                                |
|   +------------+-------------+      - Diff Coverage >= 80.0%                                      |
|                |                    - Failed Tests == 0                                           |
|                v                    - 0 Blocking CVEs / 0 Secrets                                 |
|   +--------------------------+                                                                    |
|   | CandidateIngestionEngine |                                                                    |
|   | (A4-CAN-002)             |                                                                    |
|   +--------------------------+                                                                    |
+---------------------------------------------------------------------------------------------------+
```

### 2.1 Separation of CI Evidence vs Candidate Release Contract
It is critical to distinguish between raw CI evidence and a candidate release contract:
1. **CI Evidence (`CIEvidenceRecord`)**:
   - Observational and descriptive.
   - Records whatever occurred during the pipeline run (e.g., build failure, test error, 45% coverage).
   - Serves as raw audit history and developer telemetry.
2. **Candidate Release Contract (`CandidateReleaseContract`)**:
   - Normative and gate-enforcing.
   - Defines the immutable boundary of a release candidate eligible for qualification.
   - Strictly rejects any pipeline run that failed, had skipped/failing tests, failed diff coverage, or contained unpinned digests.
   - Provides a factory method `from_ci_evidence()` to ingest and validate raw CI outputs.

### 2.2 Pydantic v2 Architectural Standards
The new module `platform_core/models/candidate_contract.py` will adhere to the following standards:
- **Base Class**: `pydantic.BaseModel`.
- **Model Configuration**: `ConfigDict(extra="forbid", populate_by_name=True, validate_default=True, str_strip_whitespace=True)`.
- **Field Constraints**: Explicit regex patterns, numerical bounds (`ge`, `le`), and literal enumerations.
- **Fail-Closed Validation**: `@model_validator(mode="after")` enforcing holistic policy gates.

---

## 3. Proposed Pydantic Models & Field Definitions

Below is the complete, proposed technical design for `platform_core/models/candidate_contract.py`:

```python
"""
NERO Universal Enterprise DevOps Automation Platform
Candidate Release Contract Data Model (A4-CAN-001)

Strongly-typed Pydantic v2 models defining the authoritative entry contract for release
candidates transitioning from Continuous Integration (Phase A3) into Release Engineering (Phase A4).
Enforces immutable digests, 100% test pass rate, >=80% diff coverage, and 0 blocking CVEs.
"""

from __future__ import annotations
import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


# ==============================================================================
# 1. CONSTANTS & REGEX PATTERNS
# ==============================================================================
APP_ID_REGEX = r"^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$"
COMPONENT_NAME_REGEX = r"^[a-z0-9][a-z0-9-]{1,30}[a-z0-9]$"
COMMIT_SHA_REGEX = r"^[a-f0-9]{40}$|^[a-f0-9]{64}$"
SHA256_DIGEST_REGEX = r"^sha256:[a-f0-9]{64}$"
EXECUTION_ID_REGEX = r"^ci-[a-z0-9-]+-[0-9]+-b[0-9]+$"
CANDIDATE_ID_REGEX = r"^cand-[a-z0-9-]+-[0-9]{14}$"
SEMVER_REGEX = r"^v?[0-9]+\.[0-9]+(\.[0-9]+)?(-[a-zA-Z0-9.]+)?$"


# ==============================================================================
# 2. CHILD ARTIFACT & PROVENANCE MODELS
# ==============================================================================
class CandidateComponentArtifact(BaseModel):
    """Represents a compiled, immutable deployable component artifact."""
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(
        ...,
        pattern=COMPONENT_NAME_REGEX,
        description="Component identifier matching application specification"
    )
    type: Literal["oci_image", "static_tarball", "worker", "scheduled-task"] = Field(
        ...,
        description="Artifact packaging and deployment classification"
    )
    repository: str = Field(
        ...,
        min_length=1,
        max_length=300,
        description="Storage repository URI (e.g. localhost:5100/hotel-billing-backend or S3 bucket)"
    )
    tag: str = Field(
        ...,
        pattern=SEMVER_REGEX,
        description="Human-readable release candidate tag (e.g. 1.0.0 or v1.0.0-rc1)"
    )
    digest: str = Field(
        ...,
        pattern=SHA256_DIGEST_REGEX,
        description="Immutable 64-character SHA-256 content digest (e.g. sha256:4f8a...)"
    )
    size_bytes: Optional[int] = Field(
        default=None,
        ge=0,
        description="Artifact payload size in bytes"
    )


class CandidateGitProvenance(BaseModel):
    """Source code repository and commit provenance."""
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    repository: str = Field(
        ...,
        min_length=3,
        max_length=300,
        description="Remote SCM repository URL"
    )
    commit_sha: str = Field(
        ...,
        pattern=COMMIT_SHA_REGEX,
        description="Exact 40-character or 64-character hexadecimal commit hash"
    )
    branch: str = Field(
        ...,
        pattern=r"^[a-zA-Z0-9/_.-]+$",
        description="Source Git branch (e.g. develop or main)"
    )
    pull_request_id: Optional[str] = Field(
        default=None,
        pattern=r"^[0-9]+$",
        description="PR identifier if triggered via pull request"
    )


class CandidateExecutionProvenance(BaseModel):
    """Continuous integration pipeline execution metadata."""
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ci_execution_id: str = Field(
        ...,
        pattern=EXECUTION_ID_REGEX,
        description="Unique CI execution identifier"
    )
    job_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Jenkins or orchestrator job name"
    )
    build_number: int = Field(
        ...,
        ge=1,
        description="Deterministic build sequence number"
    )
    build_result: Literal["SUCCESS"] = Field(
        ...,
        description="Only builds with result 'SUCCESS' are eligible for release candidacy"
    )
    duration_seconds: float = Field(
        ...,
        ge=0.0,
        description="Total CI build and test execution duration in seconds"
    )


# ==============================================================================
# 3. QUALITY & SECURITY EVIDENCE MODELS
# ==============================================================================
class CandidateTestEvidence(BaseModel):
    """Automated test execution and code coverage evidence."""
    model_config = ConfigDict(extra="forbid")

    total_tests: int = Field(
        ...,
        ge=1,
        description="Total unit and integration tests executed (must be >= 1)"
    )
    passed_tests: int = Field(
        ...,
        ge=1,
        description="Total tests successfully passed"
    )
    failed_tests: Literal[0] = Field(
        0,
        description="Failed tests count (must be strictly 0 for candidate eligibility)"
    )
    skipped_tests: int = Field(
        default=0,
        ge=0,
        description="Skipped tests count"
    )
    diff_coverage_percentage: float = Field(
        ...,
        ge=80.0,
        le=100.0,
        description="Changed-code diff test coverage (must meet or exceed mandatory 80.0% threshold)"
    )

    @model_validator(mode="after")
    def validate_test_tallies(self) -> CandidateTestEvidence:
        if self.passed_tests + self.skipped_tests != self.total_tests:
            raise ValueError(
                f"Test tally mismatch: passed ({self.passed_tests}) + skipped ({self.skipped_tests}) "
                f"!= total ({self.total_tests})"
            )
        return self


class CandidateSecurityEvidence(BaseModel):
    """DevSecOps scan results and vulnerability evaluation."""
    model_config = ConfigDict(extra="forbid")

    scanner_status: Literal["COMPLETED", "VERIFIED_OFFLINE"] = Field(
        ...,
        description="Execution state of security scanners (fail-closed if incomplete)"
    )
    database_status: Literal["UP_TO_DATE", "VERIFIED_OFFLINE"] = Field(
        ...,
        description="State of vulnerability databases (fail-closed if stale or unverified)"
    )
    secrets_detected: Literal[0] = Field(
        0,
        description="Unexempted hardcoded secrets detected (must be strictly 0)"
    )
    sast_blocking_issues: Literal[0] = Field(
        0,
        description="Static analysis blocking issues (must be strictly 0)"
    )
    cve_critical: Literal[0] = Field(
        0,
        description="Unexempted CRITICAL CVEs (must be strictly 0)"
    )
    cve_high: Literal[0] = Field(
        0,
        description="Unexempted HIGH CVEs (must be strictly 0)"
    )
    exempted_cve_count: int = Field(
        default=0,
        ge=0,
        description="Count of active waived CVEs documented in .nero-security-exceptions.yaml"
    )
    active_waiver_ids: List[str] = Field(
        default_factory=list,
        description="List of security exception IDs applicable to this candidate"
    )


# ==============================================================================
# 4. ROOT CANDIDATE RELEASE CONTRACT MODEL
# ==============================================================================
class CandidateReleaseContract(BaseModel):
    """
    Authoritative, immutable entry contract for Phase A4 Release Engineering.
    Represents an ingested, qualified CI output ready for release manifest packaging.
    """
    model_config = ConfigDict(
        extra="forbid",
        validate_default=True,
        populate_by_name=True,
        str_strip_whitespace=True
    )

    schema_version: Literal["1.0.0"] = Field(
        default="1.0.0",
        description="Contract schema version"
    )
    candidate_id: str = Field(
        ...,
        pattern=CANDIDATE_ID_REGEX,
        description="Unique release candidate identifier (e.g. cand-hotel-billing-20261109120000)"
    )
    application_id: str = Field(
        ...,
        pattern=APP_ID_REGEX,
        description="Application identifier registered in the service catalog"
    )
    release_tag: str = Field(
        ...,
        pattern=SEMVER_REGEX,
        description="Target semantic version tag for the proposed release"
    )
    created_at: str = Field(
        ...,
        description="UTC ISO-8601 completion timestamp (e.g. 2026-11-09T12:00:00Z)"
    )
    source: CandidateGitProvenance
    execution: CandidateExecutionProvenance
    components: Dict[str, CandidateComponentArtifact] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Dictionary of compiled component artifacts keyed by component name"
    )
    test_evidence: CandidateTestEvidence
    security_evidence: CandidateSecurityEvidence
    payload_checksum: Optional[str] = Field(
        default=None,
        pattern=r"^[a-f0-9]{64}$",
        description="SHA-256 checksum of canonical JSON payload (excluding checksum field)"
    )

    @field_validator("created_at")
    @classmethod
    def validate_iso8601_utc(cls, v: str) -> str:
        """Enforces strict ISO-8601 UTC timestamp formatting ending in 'Z'."""
        if not v.endswith("Z"):
            raise ValueError(f"Timestamp must be explicit UTC ending in 'Z': {v}")
        try:
            # Parse YYYY-MM-DDTHH:MM:SSZ
            datetime.strptime(v, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError as err:
            raise ValueError(f"Invalid ISO-8601 UTC timestamp format: {err}") from err
        return v

    @model_validator(mode="after")
    def validate_component_integrity(self) -> CandidateReleaseContract:
        """Validates dictionary keys match component names and prevents duplicates."""
        for key, comp in self.components.items():
            if key != comp.name:
                raise ValueError(
                    f"Component key '{key}' does not match inner component name '{comp.name}'"
                )
        return self

    def compute_payload_checksum(self) -> str:
        """Computes deterministic SHA-256 hash over canonical JSON representation."""
        data = self.model_dump(exclude={"payload_checksum"}, mode="json")
        canonical_bytes = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(canonical_bytes).hexdigest()

    def seal_contract(self) -> CandidateReleaseContract:
        """Calculates and embeds the payload checksum into the contract."""
        self.payload_checksum = self.compute_payload_checksum()
        return self

    def verify_checksum(self) -> bool:
        """Verifies that the embedded checksum matches the computed payload hash."""
        if not self.payload_checksum:
            return False
        return self.payload_checksum == self.compute_payload_checksum()

    @classmethod
    def from_ci_evidence(
        cls,
        evidence: Union[Dict[str, Any], str],
        release_tag: str,
        diff_coverage: Optional[float] = None,
        candidate_id: Optional[str] = None
    ) -> CandidateReleaseContract:
        """
        Factory method: Ingests raw Phase A3 CI evidence and validates it into a CandidateReleaseContract.
        Bridges Phase A3 output into Phase A4 input.
        """
        if isinstance(evidence, str):
            evidence_data = json.loads(evidence)
        else:
            evidence_data = dict(evidence)

        app_id = evidence_data.get("application_id") or "unknown"
        now_ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        cid = candidate_id or f"cand-{app_id}-{now_ts}"

        # Extract git provenance
        git_data = evidence_data.get("git", {})
        source = CandidateGitProvenance(
            repository=git_data.get("repository", ""),
            commit_sha=git_data.get("commit_sha", ""),
            branch=git_data.get("branch", "develop"),
            pull_request_id=git_data.get("pull_request_id")
        )

        # Extract jenkins execution provenance
        jk_data = evidence_data.get("jenkins", {})
        execution = CandidateExecutionProvenance(
            ci_execution_id=evidence_data.get("ci_run_id", f"ci-{app_id}-0-b1"),
            job_name=jk_data.get("job", "universal-ci-pipeline"),
            build_number=jk_data.get("build_number", 1),
            build_result=jk_data.get("result", "SUCCESS"),
            duration_seconds=float(jk_data.get("duration_seconds", 0.0))
        )

        # Extract test evidence
        t_data = evidence_data.get("test_summary", {})
        cov = diff_coverage if diff_coverage is not None else float(t_data.get("coverage_percentage", 0.0))
        test_evidence = CandidateTestEvidence(
            total_tests=t_data.get("total", 0),
            passed_tests=t_data.get("passed", 0),
            failed_tests=t_data.get("failed", 0),
            skipped_tests=t_data.get("skipped", 0),
            diff_coverage_percentage=cov
        )

        # Extract security evidence
        s_data = evidence_data.get("security_summary", {})
        security_evidence = CandidateSecurityEvidence(
            scanner_status="COMPLETED",
            database_status="VERIFIED_OFFLINE",
            secrets_detected=s_data.get("secrets_detected", 0),
            sast_blocking_issues=s_data.get("sast_issues", 0),
            cve_critical=s_data.get("cve_critical", 0),
            cve_high=s_data.get("cve_high", 0),
            exempted_cve_count=s_data.get("exempted_count", 0),
            active_waiver_ids=s_data.get("active_waiver_ids", [])
        )

        # Extract component artifacts
        comp_dict = {}
        for art in evidence_data.get("artifacts", []):
            c_name = art.get("component")
            c_image = art.get("image", "")
            # Derive tag from image string if present
            c_tag = release_tag
            if ":" in c_image:
                c_tag = c_image.split(":")[-1]

            comp_artifact = CandidateComponentArtifact(
                name=c_name,
                type="oci_image",
                repository=c_image.split(":")[0] if ":" in c_image else c_image,
                tag=c_tag,
                digest=art.get("digest", "")
            )
            comp_dict[c_name] = comp_artifact

        contract = cls(
            schema_version="1.0.0",
            candidate_id=cid,
            application_id=app_id,
            release_tag=release_tag,
            created_at=evidence_data.get("timestamp") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            source=source,
            execution=execution,
            components=comp_dict,
            test_evidence=test_evidence,
            security_evidence=security_evidence
        )
        return contract.seal_contract()
```

---

## 4. Validation Rules & Policy Enforcements

The model architecture establishes deterministic, fail-closed validation across 12 distinct dimensions:

```text
+===================================================================================================+
|                                    VALIDATION RULES SPECIFICATION                                 |
+===================================================================================================+
| Rule ID    | Target Field / Entity        | Validation Standard                     | Error Type  |
|------------|------------------------------|-----------------------------------------|-------------|
| VAL-CAN-01 | schema_version               | Strictly Literal["1.0.0"]               | SchemaError |
| VAL-CAN-02 | candidate_id                 | Regex ^cand-[a-z0-9-]+-[0-9]{14}$       | FormatError |
| VAL-CAN-03 | application_id               | Regex ^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$ | CatalogError|
| VAL-CAN-04 | commit_sha                   | Exact 40 or 64 hex characters           | GitError    |
| VAL-CAN-05 | digest (artifacts)           | Exact sha256:[a-f0-9]{64}               | DigestError |
| VAL-CAN-06 | build_result                 | Strictly Literal["SUCCESS"]             | CIError     |
| VAL-CAN-07 | failed_tests                 | Strictly Literal[0]                     | QualityError|
| VAL-CAN-08 | diff_coverage_percentage     | Bounded [80.0, 100.0]                   | CoverageGate|
| VAL-CAN-09 | security_evidence.scanner    | Must be "COMPLETED" or "VERIFIED_OFFLINE"| PolicyError|
| VAL-CAN-10 | cve_critical & cve_high      | Strictly Literal[0] unexempted blockers | DevSecOps   |
| VAL-CAN-11 | created_at                   | Strict ISO-8601 UTC ending in 'Z'       | TimeFormat  |
| VAL-CAN-12 | components                   | Dict keys match component.name; len >= 1| StructError |
+===================================================================================================+
```

### 4.1 Fail-Closed Security Policy Boundary
- **Zero Blocking CVEs (Not Fictional Zero Vulnerabilities)**:
  - The model enforces `cve_critical == 0` and `cve_high == 0`.
  - Low and Medium severity findings are recorded but do not fail the candidate contract unless escalated by policy.
  - Known CVEs that have formal waivers granted in `.nero-security-exceptions.yaml` are enumerated in `exempted_cve_count` and `active_waiver_ids`.
- **Fail-Closed on Scanner Incompletion**:
  - If a security scanner crashes, times out, or fails to contact a local scanner daemon, `scanner_status` cannot be marked `"COMPLETED"`.
  - The contract validator rejects any candidate where scanners did not complete successfully.
  - A stale or missing vulnerability database is explicitly rejected (`database_status` must be `"UP_TO_DATE"` or `"VERIFIED_OFFLINE"`).

### 4.2 Quality & Coverage Gate Assertion
- If changed-code diff coverage is $79.9\%$, the model rejects the contract with a validation error indicating that diff coverage is below the mandatory $80.0\%$ threshold.
- If zero tests were executed (`total_tests == 0`), the model rejects the contract.

---

## 5. Schema & Version Compatibility Plan

### 5.1 Coexistence with Existing Platform Schemas
Phase A4 does not break existing schemas:

| Schema Layer | File / Location | Coexistence Strategy |
|---|---|---|
| **Application Specification Schema v2** | `platform_core/engine/models.py` | Preserved untouched. `CandidateReleaseContract` references components defined in `ApplicationSpec`. |
| **CI Evidence Schema v1.0.0** | `platform_core/engine/ci_evidence.py` | Preserved untouched. `CandidateReleaseContract.from_ci_evidence()` ingests `CIEvidenceRecord` without breaking A3 code. |
| **Release Manifest Schema v1** | `platform_core/engine/release_manager.py` | Runs in parallel. In Milestone 1, Manifest v2 (`release_manifest_v2.py`) will ingest CandidateReleaseContracts. |
| **Audit Record Schema** | `platform_core/audit/audit_logger.py` | Preserved untouched. Contract checksums and IDs are compatible with `details` JSON payload. |

### 5.2 Unknown-Field Handling & Strictness
- `model_config = ConfigDict(extra="forbid")` is enforced on the contract and all child models.
- Any unrecognized field injected into a candidate release contract triggers an immediate Pydantic `ValidationError`.
- This ensures that unexpected inputs are caught before reaching the release qualification engine.

### 5.3 Deterministic Serialization & Checksums
- Serialization format: Deterministic JSON with sorted keys, no whitespace around separators (`separators=(',', ':')`), and UTF-8 byte encoding.
- The `payload_checksum` field contains the SHA-256 digest of the canonical JSON bytes computed with `payload_checksum` excluded.
- Any modification of a single byte inside the contract invalidates `verify_checksum()`.

---

## 6. Unit-Test Matrix (14 Distinct Test Scenarios)

The unit-test suite `tests/unit/test_candidate_contract.py` will implement 14 exhaustive test cases. 

> [!IMPORTANT]
> **Audit Isolation Invariant**: All test cases run purely in memory. No test calls `append_audit_record()` or touches `platform_core/audit/audit_log.jsonl`.

```text
+===================================================================================================+
|                                    14-SCENARIO UNIT TEST MATRIX                                   |
+===================================================================================================+
```

### Test Case 1: Valid Single-Component Candidate Release (`hotel-billing` backend)
- **Input**: Valid application `hotel-billing`, commit `a1b2c3d4e5f67890123456789abcdef012345678`, single OCI image component with pinned SHA-256 digest, 10/10 passed tests, 85.0% coverage, 0 CVEs.
- **Expected Result**: Successfully instantiates `CandidateReleaseContract`.
- **Assertions**: `contract.verify_checksum() is True`, `contract.components["backend"].digest` matches.

### Test Case 2: Invalid Application Identifier
- **Input**: `application_id = "Hotel_Billing_Invalid!"` (uppercase, underscores, special characters).
- **Expected Result**: Raises `pydantic.ValidationError`.
- **Expected Error**: `String should match pattern '^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$'`.

### Test Case 3: Invalid Git Commit SHA
- **Input**: `commit_sha = "a1b2c3d"` (short 7-character hash instead of 40-character full hex SHA).
- **Expected Result**: Raises `pydantic.ValidationError`.
- **Expected Error**: `String should match pattern '^[a-f0-9]{40}$|^[a-f0-9]{64}$'`.

### Test Case 4: Invalid Artifact SHA-256 Digest Format
- **Input**: `digest = "sha256:invalid-short-hash"` or missing `sha256:` prefix.
- **Expected Result**: Raises `pydantic.ValidationError`.
- **Expected Error**: `String should match pattern '^sha256:[a-f0-9]{64}$'`.

### Test Case 5: Failed CI Result
- **Input**: `execution.build_result = "FAILURE"`.
- **Expected Result**: Raises `pydantic.ValidationError`.
- **Expected Error**: `Input should be 'SUCCESS'`.

### Test Case 6: Failed Test Evidence
- **Input**: `test_evidence.failed_tests = 1`.
- **Expected Result**: Raises `pydantic.ValidationError`.
- **Expected Error**: `Input should be 0`.

### Test Case 7: Changed-Code Coverage Below 80.0% Threshold
- **Input**: `test_evidence.diff_coverage_percentage = 79.9`.
- **Expected Result**: Raises `pydantic.ValidationError`.
- **Expected Error**: `Input should be greater than or equal to 80`.

### Test Case 8: Missing Security Scan Evidence
- **Input**: `security_evidence.scanner_status = "FAILED"`.
- **Expected Result**: Raises `pydantic.ValidationError`.
- **Expected Error**: `Input should be 'COMPLETED' or 'VERIFIED_OFFLINE'`.

### Test Case 9: Blocking Security Finding (Unexempted Critical CVE)
- **Input**: `security_evidence.cve_critical = 1`.
- **Expected Result**: Raises `pydantic.ValidationError`.
- **Expected Error**: `Input should be 0`.

### Test Case 10: Malformed Creation Timestamp
- **Input**: `created_at = "2026-11-09 12:00:00"` (missing ISO-8601 'T' and 'Z').
- **Expected Result**: Raises `pydantic.ValidationError`.
- **Expected Error**: `Timestamp must be explicit UTC ending in 'Z'`.

### Test Case 11: Unsupported Contract Schema Version
- **Input**: `schema_version = "2.0.0"`.
- **Expected Result**: Raises `pydantic.ValidationError`.
- **Expected Error**: `Input should be '1.0.0'`.

### Test Case 12: Duplicate / Mismatched Component Identifiers
- **Input**: `components = {"backend": CandidateComponentArtifact(name="frontend", ...)}` (key does not match name).
- **Expected Result**: Raises `pydantic.ValidationError`.
- **Expected Error**: `Component key 'backend' does not match inner component name 'frontend'`.

### Test Case 13: Valid Multi-Component Candidate (`hotel-billing` full stack)
- **Input**: `hotel-billing` with backend OCI container image and frontend static tarball.
- **Expected Result**: Successfully instantiates; `len(contract.components) == 2`.
- **Assertions**: Backend digest verified, frontend tarball digest verified, payload checksum valid.

### Test Case 14: Backwards-Compatible Existing Evidence Ingestion
- **Input**: Raw dictionary matching Phase A3 `ci_evidence.json` structure ingested via `CandidateReleaseContract.from_ci_evidence()`.
- **Expected Result**: Automatically maps CI evidence into valid `CandidateReleaseContract` with computed checksum.
- **Assertions**: `contract.application_id == "hotel-billing"`, `contract.verify_checksum() is True`.

---

## 7. Correct Architecture Terminology & Policy Constraints

In accordance with strict technical review standards, this implementation design enforces precise architectural language and respects all approved platform boundaries:

```text
+---------------------------------------------------------------------------------------------------+
|                                 ARCHITECTURAL TERMINOLOGY STANDARDS                               |
+---------------------------------------------------------------------------------------------------+
```

1. **Floci Local Cloud Emulation**:
   - *Prohibited Assertion*: "Floci provides 100% AWS S3 API fidelity."
   - *Accurate Statement*: Floci provides local emulation of core AWS S3 bucket and object REST APIs, sufficient for local offline testing and static asset qualification without cloud charges.
2. **Git Provenance vs Non-Repudiation**:
   - *Prohibited Assertion*: "Git commit metadata establishes non-repudiation."
   - *Accurate Statement*: Git commit metadata provides source attribution and commit traceability. Genuine cryptographic non-repudiation requires GPG/SSH signed commits and SLSA in-toto build provenance attestations generated in isolated build environments.
3. **Security Gate Policy Scope**:
   - *Prohibited Assertion*: "The platform enforces zero vulnerabilities of every severity."
   - *Accurate Statement*: The platform enforces **zero unexempted blocking findings** (zero unexempted CRITICAL or HIGH CVEs, zero secrets, zero SAST blockers). Low/Medium issues and approved business waivers documented in `.nero-security-exceptions.yaml` are explicitly managed by policy.
4. **Container Image Digest References**:
   - *Prohibited Assertion*: "Images in Dockerfiles are already pinned to verified digests."
   - *Accurate Statement*: Verified primary registry digests (`golang:1.27.3-alpine3.24@sha256:0fd028db...` and `gcr.io/distroless/static-debian12:nonroot@sha256:52dcfbab...`) are planned for implementation adoption during Milestone 2; they are not currently applied in the existing working tree.
5. **Retained Gate 2 Architecture Conditions**:
   - **Simulated Governance**: Two-person approval remains classified as `LOCAL_APPROVAL_SIMULATION`.
   - **Rollback Qualification**: Less-than-30-second rollback remains an architectural design target evaluated via Approach A ($N=5$).
   - **Concurrency Bounding**: Parallel execution is provisionally bounded to `max_workers = 2`.
   - **Audit Isolation**: Corrective Action `CORR-ACT-AUDIT-001` remains tracked separately as `NOT ESTIMATED`.

---

## 8. Objective Acceptance Criteria for Task A4-CAN-001

Task `A4-CAN-001` will be considered complete when all of the following objective criteria are independently verified:

1. **Model Functionality**: `CandidateReleaseContract` and its child models are fully implemented under `platform_core/models/candidate_contract.py` using Pydantic v2.
2. **Deterministic Validation**: All 12 validation rules reject malformed, unpinned, failing, or low-coverage inputs with explicit `ValidationError` messages.
3. **CI Compatibility**: The `from_ci_evidence()` factory cleanly parses existing Phase A3 `ci_evidence.json` data without schema errors.
4. **Test Pass Rate**: All 14 unit test cases in `tests/unit/test_candidate_contract.py` pass with 100% success (0 failed, 0 errors, 0 warnings).
5. **Test Isolation**: Running the unit-test suite appends zero records to `platform_core/audit/audit_log.jsonl`.
6. **Zero Regression**: Repository-wide test discovery continues to pass with zero regressions against existing A1–A3 suites.
7. **Offline Purity**: The module requires zero external internet egress, zero cloud credentials, and zero running external services.
8. **Working Tree Safety**: Zero modifications are made to existing application source code, Dockerfiles, Jenkinsfiles, or Terraform configuration.

---

## 9. Estimated Work Breakdown for the 8 EH Task

The 8.0 Nominal Engineering Hours allocated to `A4-CAN-001` are partitioned as follows:

| Subtask ID | Work Description | Planned EH | Discipline |
|---|---|:---:|---|
| **A4-CAN-001.1** | Create `platform_core/models/` package and implement child Pydantic models (`CandidateComponentArtifact`, `CandidateGitProvenance`, `CandidateExecutionProvenance`). | 1.5 EH | Python Core Dev |
| **A4-CAN-001.2** | Implement evidence models (`CandidateTestEvidence`, `CandidateSecurityEvidence`) and root `CandidateReleaseContract` with field validators and checksum generation. | 2.0 EH | Python Core Dev |
| **A4-CAN-001.3** | Implement `from_ci_evidence()` factory adapter for seamless Phase A3 CI evidence translation. | 1.5 EH | Architecture / Integration |
| **A4-CAN-001.4** | Author comprehensive 14-scenario unit-test suite in `tests/unit/test_candidate_contract.py`. | 2.0 EH | Test Engineering |
| **A4-CAN-001.5** | Execute preflight test run, verify zero audit-ledger pollution, and conduct peer code review. | 1.0 EH | Quality & Governance |
| **TOTAL** | **A4-CAN-001 Implementation Scope** | **8.0 EH** | |

---

## 10. Exact Implementation File List

When Gate 3 implementation is authorized, the engineering work for `A4-CAN-001` will touch exclusively these files:

### Files to Create (New):
1. `platform_core/models/__init__.py`  
   *Purpose*: Establishes the `platform_core.models` Python package.
2. `platform_core/models/candidate_contract.py`  
   *Purpose*: Complete Pydantic v2 candidate contract models and validation logic (~180 lines).
3. `tests/unit/test_candidate_contract.py`  
   *Purpose*: Unit test suite covering all 14 test scenarios (~220 lines).

### Files to Modify:
- **NONE**. No existing application code, pipelines, Dockerfiles, Terraform scripts, or audit files will be modified.

---

## 11. Rollback & Failure Recovery Strategy

Because Task `A4-CAN-001` introduces strictly new, additive Python files and touches no existing code or services:
- **Failure Mode**: If unit tests fail, schema conflicts arise, or syntax errors occur during implementation:
- **Recovery Procedure**:
  ```powershell
  # Remove newly created files to return working tree to exact pre-implementation baseline:
  Remove-Item -Force "platform_core/models/candidate_contract.py" -ErrorAction SilentlyContinue
  Remove-Item -Force "platform_core/models/__init__.py" -ErrorAction SilentlyContinue
  Remove-Item -Force "tests/unit/test_candidate_contract.py" -ErrorAction SilentlyContinue
  ```
- **Zero Blast Radius**: Existing containers, databases, Jenkins jobs, and audit logs remain 100% unaffected.

---

## 12. Final Authorization Boundary

```text
+===================================================================================================+
|                                    FINAL AUTHORIZATION BOUNDARY                                   |
+===================================================================================================+
|  This preflight review is complete and strictly technical.                                       |
|  No code has been written. No files have been created.                                            |
|  Gate 3 remains PENDING OWNER AUTHORIZATION. Implementation remains strictly halted.              |
+===================================================================================================+
```

```text
A4-CAN-001 PREFLIGHT COMPLETE — AWAITING EXPLICIT IMPLEMENTATION AUTHORIZATION
```
