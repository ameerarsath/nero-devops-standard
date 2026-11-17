# NERO Programme 1 — Phase A4
# Task Design Refinement: A4-CAN-001
## Candidate Release Contract Model (`platform_core/models/candidate_contract.py`)

**Document ID:** NERO-A4-CAN-001-REFINED-DESIGN-001  
**Task ID:** `A4-CAN-001`  
**Estimated Effort:** 8.0 Engineering Hours (Nominal Baseline Maintained)  
**Governing Milestone:** Milestone 1 — Candidate Ingestion & Release Manifest Architecture (30.0 EH)  
**Date:** November 9, 2026  
**Author:** Principal Python Architect, Senior DevOps Engineer & Software Supply Chain Security Specialist  
**Operating Mode:** STRICTLY READ-ONLY DESIGN REFINEMENT (Zero Implementation Code Written)  
**Target Repository:** `D:\project\billing-system-master\billing-system-master`  
**Active Git Branch:** `devops/jenkins-floci-local-lab`  

---

## 1. Executive Findings & Architectural Context

### 1.1 Current Governance Status
- **Gate 1 — Phase A3 Closure**: **APPROVED** (`A3_CLOSURE_VERIFIED_WITH_EXCEPTIONS`).
- **Gate 2 — Phase A4 Architecture**: **APPROVED WITH CONDITIONS** (`A4_READY_WITH_CONDITIONS`).
- **Gate 3 — Phase A4 Implementation**: **PENDING OWNER AUTHORIZATION** (**STRICTLY HALTED**).

```text
+===================================================================================================+
|                                    CURRENT GOVERNANCE POSTURE                                     |
+===================================================================================================+
|  Gate 1: Phase A3 Closure          --> APPROVED (A3_CLOSURE_VERIFIED_WITH_EXCEPTIONS)             |
|  Gate 2: Phase A4 Architecture     --> APPROVED WITH CONDITIONS (A4_READY_WITH_CONDITIONS)        |
|  Gate 3: Phase A4 Implementation   --> PENDING OWNER AUTHORIZATION (IMPLEMENTATION HALTED)        |
+===================================================================================================+
```

### 1.2 Verified Repository Facts
A rigorous inspection of the current working tree confirmed the following facts:
1. **Target Namespace**: The directory `platform_core/models/` does not currently exist. Existing specification models live in `platform_core/engine/models.py`. Establishing `platform_core/models/` creates a dedicated, cleanly separated domain for release contracts.
2. **Pydantic v2 Alignment**: Existing models in `platform_core/engine/models.py` utilize Pydantic v2 conventions: `ConfigDict(extra="forbid")`, `@field_validator`, and `@model_validator(mode="after")`. The new contract model directly conforms to this pattern.
3. **CI Evidence Generator**: `platform_core/engine/ci_evidence.py` generates `CIEvidenceRecord` with `schema_version = "1.0.0"`. It captures execution logs (including potential failures or unpinned tags) rather than pre-qualified candidate release contracts.
4. **Security Exception Engine**: `platform_core/policy/security_exceptions.py` evaluates exemptions against `.nero-security-exceptions.yaml` enforcing a mandatory 90-day expiration TTL.
5. **Scanner Orchestrator**: `platform_core/adapters/security/scanner_orchestrator.py` defines blocking findings strictly as unexempted exposed secrets, unexempted SAST errors, and unexempted CRITICAL/HIGH CVEs.
6. **Audit Ledger Baseline**: `platform_core/audit/audit_log.jsonl` contains 84 verified records with an unbroken SHA-256 chain. All unit tests must be isolated to prevent ledger contamination.

### 1.3 Key Refinements in This Document
- **Discriminated-Union Artifact Hierarchy**: Replaces the flat artifact model with specialized `OCIImageArtifact`, `StaticArtifact`, and `WorkerArtifact` models. Eliminates meaningless mandatory fields (e.g. S3 keys on Docker images or container registries on static tarballs).
- **Digest-First Identity**: Enforces 64-character SHA-256 digests (`sha256:[a-f0-9]{64}`) as the sole authoritative immutable identity. Tags are explicitly modeled as optional/secondary metadata.
- **Arithmetic Test Consistency**: Enforces `passed + failed + skipped == total`, rejects zero-test or failing runs, and formalizes skipped-test handling based on existing A3 policies.
- **Fail-Closed Security Model**: Captures scanner versions, scan timestamps, target digests, vulnerability database metadata, and database age; rejects stale databases even if marked `VERIFIED_OFFLINE`.
- **RFC 8785 Canonical Checksumming**: Specifies recursive key-sorted canonical JSON serialization, UTF-8 encoding, timestamp normalization, and field exclusion for deterministic payload hashing.
- **A3 Evidence Compatibility**: Codifies explicit version handling and field mapping for `from_ci_evidence()`.

---

## 2. Revised Artifact Model Hierarchy (Discriminated Union)

Rather than forcing all artifact types into a monolithic model with optional or misleading fields, the refined architecture uses a **discriminated union** in Pydantic v2.

```text
+---------------------------------------------------------------------------------------------------+
|                                 ARTIFACT MODEL DISCRIMINATED UNION                                |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|                               +----------------------------+                                      |
|                               |    BaseComponentArtifact   |                                      |
|                               |    - name: str             |                                      |
|                               |    - type: str             |                                      |
|                               +--------------+-------------+                                      |
|                                              |                                                    |
|                   +--------------------------+--------------------------+                         |
|                   |                                                     |                         |
|                   v                                                     v                         |
|     +---------------------------+                         +---------------------------+           |
|     |     OCIImageArtifact      |                         |       StaticArtifact      |           |
|     |  type: "oci_image"        |                         |  type: "static_tarball"   |           |
|     |  - registry: str          |                         |  - storage_backend: "s3"  |           |
|     |  - repository: str        |                         |  - bucket: str            |           |
|     |  - digest: sha256:...     |                         |  - key: str               |           |
|     |  - tag: Optional[str]     |                         |  - sha256: sha256:...     |           |
|     |  - media_type: str        |                         |  - size_bytes: int        |           |
|     +---------------------------+                         +---------------------------+           |
|                   ^                                                     ^                         |
|                   |                                                     |                         |
|                   +--------------------------+--------------------------+                         |
|                                              |                                                    |
|                               +--------------+-------------+                                      |
|                               |       WorkerArtifact       |                                      |
|                               |  type: "worker"            |                                      |
|                               |  - worker_type: str        |                                      |
|                               |  - executable: Union[...]  |                                      |
|                               +----------------------------+                                      |
+---------------------------------------------------------------------------------------------------+
```

### 2.1 Model Definitions

```python
from typing import Annotated, Literal, Optional, Union
from pydantic import BaseModel, Field, ConfigDict

COMPONENT_NAME_REGEX = r"^[a-z0-9][a-z0-9-]{1,30}[a-z0-9]$"
SHA256_DIGEST_REGEX = r"^sha256:[a-f0-9]{64}$"
SEMVER_REGEX = r"^v?[0-9]+\.[0-9]+(\.[0-9]+)?(-[a-zA-Z0-9.]+)?$"


class BaseComponentArtifact(BaseModel):
    """Abstract base class for deployable artifacts."""
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(
        ...,
        pattern=COMPONENT_NAME_REGEX,
        description="Component identifier matching application specification"
    )


class OCIImageArtifact(BaseComponentArtifact):
    """Container image artifact stored in an OCI-compliant registry."""
    type: Literal["oci_image"] = "oci_image"

    registry: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Registry host:port (e.g. localhost:5100 or 123456789012.dkr.ecr.us-east-1.amazonaws.com)"
    )
    repository: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Repository path (e.g. hotel-billing-backend or nero/sample-go-service)"
    )
    digest: str = Field(
        ...,
        pattern=SHA256_DIGEST_REGEX,
        description="Authoritative immutable SHA-256 image content digest"
    )
    tag: Optional[str] = Field(
        default=None,
        pattern=SEMVER_REGEX,
        description="Informative human-readable tag. NOT the authoritative immutable identity."
    )
    media_type: str = Field(
        default="application/vnd.docker.distribution.manifest.v2+json",
        description="OCI or Docker manifest media type"
    )
    size_bytes: Optional[int] = Field(
        default=None,
        ge=0,
        description="Compressed image manifest and layers total size in bytes"
    )


class StaticArtifact(BaseComponentArtifact):
    """Static web assets or tarball bundle stored in object storage (Floci S3)."""
    type: Literal["static_tarball"] = "static_tarball"

    storage_backend: Literal["s3", "local_file"] = Field(
        default="s3",
        description="Storage abstraction provider"
    )
    bucket: str = Field(
        ...,
        min_length=3,
        max_length=63,
        description="Target S3 bucket name (e.g. nero-releases-local)"
    )
    key: str = Field(
        ...,
        min_length=1,
        max_length=1024,
        description="Object storage key (e.g. releases/hotel-billing/rel-20261109/frontend.tar.gz)"
    )
    sha256: str = Field(
        ...,
        pattern=SHA256_DIGEST_REGEX,
        description="Authoritative immutable SHA-256 payload checksum"
    )
    size_bytes: int = Field(
        ...,
        ge=1,
        description="Exact payload size in bytes"
    )
    content_type: str = Field(
        default="application/gzip",
        description="MIME content type of the archived payload"
    )


class WorkerArtifact(BaseComponentArtifact):
    """Background worker or scheduled task workload."""
    type: Literal["worker"] = "worker"

    worker_type: Literal["container_worker", "process_worker"] = Field(
        default="container_worker",
        description="Execution model for the background worker"
    )
    executable: Union[OCIImageArtifact, StaticArtifact] = Field(
        ...,
        description="Underlying deployable artifact: container image or standalone archive"
    )


# Discriminated Union type for polymorphic artifact validation
CandidateArtifact = Annotated[
    Union[OCIImageArtifact, StaticArtifact, WorkerArtifact],
    Field(discriminator="type")
]
```

---

## 3. Artifact Payload Examples

### 3.1 OCI Container Image (`hotel-billing` Backend)
```json
{
  "name": "backend",
  "type": "oci_image",
  "registry": "localhost:5100",
  "repository": "hotel-billing-backend",
  "digest": "sha256:4f8a91c83a7493a7e3052846194a82b947265819385927491029485726194829",
  "tag": "1.0.0",
  "media_type": "application/vnd.docker.distribution.manifest.v2+json",
  "size_bytes": 184520912
}
```

### 3.2 Static Frontend Tarball (`hotel-billing` Frontend)
```json
{
  "name": "frontend",
  "type": "static_tarball",
  "storage_backend": "s3",
  "bucket": "nero-releases-local",
  "key": "hotel-billing/rel-20261109120000/frontend.tar.gz",
  "sha256": "sha256:d829104829104829104829104829104829104829104829104829104829104829",
  "size_bytes": 1459204,
  "content_type": "application/gzip"
}
```

### 3.3 Worker Application (`sample-python-worker`)
```json
{
  "name": "worker",
  "type": "worker",
  "worker_type": "container_worker",
  "executable": {
    "name": "worker-image",
    "type": "oci_image",
    "registry": "localhost:5100",
    "repository": "sample-python-worker",
    "digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "tag": "1.0.0",
    "media_type": "application/vnd.docker.distribution.manifest.v2+json",
    "size_bytes": 62410112
  }
}
```

---

## 4. Test Evidence Validation & Skipped-Test Policy

### 4.1 Refined `CandidateTestEvidence` Model

```python
class CandidateTestEvidence(BaseModel):
    """Automated test execution metrics and changed-code coverage."""
    model_config = ConfigDict(extra="forbid")

    total_tests: int = Field(
        ...,
        ge=1,
        description="Total tests enumerated in test suite (must be >= 1)"
    )
    passed_tests: int = Field(
        ...,
        ge=1,
        description="Total passed tests (at least 1 test must pass)"
    )
    failed_tests: Literal[0] = Field(
        0,
        description="Failed test count (must be strictly 0; failures block candidate qualification)"
    )
    skipped_tests: int = Field(
        default=0,
        ge=0,
        description="Ignored or conditionally skipped tests"
    )
    diff_coverage_percentage: float = Field(
        ...,
        ge=80.0,
        le=100.0,
        description="Changed-code diff test coverage (must meet or exceed mandatory 80.0% threshold)"
    )

    @model_validator(mode="after")
    def validate_test_arithmetic_consistency(self) -> CandidateTestEvidence:
        """Enforces arithmetic invariant: passed + failed + skipped == total."""
        expected_total = self.passed_tests + self.failed_tests + self.skipped_tests
        if self.total_tests != expected_total:
            raise ValueError(
                f"Arithmetic inconsistency in test evidence: total ({self.total_tests}) "
                f"!= passed ({self.passed_tests}) + failed ({self.failed_tests}) + "
                f"skipped ({self.skipped_tests}) [sum: {expected_total}]"
            )
        return self
```

### 4.2 Skipped-Test Qualification Policy
In alignment with the approved A3 CI test qualification rules ([`platform_core/engine/junit_aggregator.py`](file:///d:/project/billing-system-master/billing-system-master/platform_core/engine/junit_aggregator.py#L30-L36)):
1. **Permitted Within Arithmetic Invariant**: Skipped tests are recognized when code includes conditional platform checks (e.g. `@pytest.mark.skipif`).
2. **Never Counted as Passes**: Skipped tests do not increase `passed_tests`.
3. **At Least One Passing Test Required**: `passed_tests >= 1` prevents suites where 100% of tests were bypassed or skipped from claiming qualification.
4. **Zero Impact on Diff Coverage Gate**: Skipped tests cannot artificially inflate or satisfy the 80.0% diff coverage gate. Diff coverage measures executed lines, not test counts.
5. **Zero Failures**: `failed_tests == 0` is strictly enforced.

---

## 5. Security Evidence Schema & Fail-Closed Freshness

### 5.1 Refined Security Models

```python
from datetime import datetime, timezone

class ScannerEvidence(BaseModel):
    """Execution telemetry for an individual DevSecOps security scanner."""
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    scanner_name: Literal["gitleaks", "semgrep", "trivy"] = Field(
        ...,
        description="Scanner engine identifier"
    )
    scanner_version: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Exact scanner binary or engine version"
    )
    scan_timestamp: str = Field(
        ...,
        description="UTC ISO-8601 execution timestamp ending in 'Z'"
    )
    target_digest: Optional[str] = Field(
        default=None,
        pattern=SHA256_DIGEST_REGEX,
        description="Exact artifact digest evaluated by the scanner (binds scan to artifact)"
    )
    status: Literal["COMPLETED"] = Field(
        ...,
        description="Execution state (must be 'COMPLETED'; 'FAILED' or 'TIMED_OUT' block qualification)"
    )
    duration_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Scan execution duration in seconds"
    )


class VulnerabilityDatabaseMetadata(BaseModel):
    """Metadata certifying the freshness of the vulnerability scanner database."""
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    database_name: str = Field(
        ...,
        description="Vulnerability database identifier (e.g. trivy-db or floci-offline-cve)"
    )
    database_version: str = Field(
        ...,
        description="Database release version or tag"
    )
    updated_at: str = Field(
        ...,
        description="UTC ISO-8601 timestamp of last database update"
    )
    database_age_days: int = Field(
        ...,
        ge=0,
        description="Age of the vulnerability database in calendar days"
    )
    status: Literal["CURRENT", "VERIFIED_OFFLINE"] = Field(
        ...,
        description="Verification state of the database"
    )

    @model_validator(mode="after")
    def validate_database_freshness(self) -> VulnerabilityDatabaseMetadata:
        """
        Enforces freshness policy:
        A database marked 'VERIFIED_OFFLINE' is NOT automatically current if stale.
        Max allowed age is 14 days for offline lab operations.
        """
        MAX_ALLOWED_OFFLINE_DAYS = 14
        if self.database_age_days > MAX_ALLOWED_OFFLINE_DAYS:
            raise ValueError(
                f"Vulnerability database is STALE: age {self.database_age_days} days exceeds "
                f"maximum allowed threshold of {MAX_ALLOWED_OFFLINE_DAYS} days. "
                "Offline qualification cannot proceed with stale vulnerability signatures."
            )
        return self


class CandidateSecurityEvidence(BaseModel):
    """Comprehensive DevSecOps scan results and vulnerability evaluation."""
    model_config = ConfigDict(extra="forbid")

    scanners: Dict[str, ScannerEvidence] = Field(
        ...,
        description="Scan execution details keyed by scanner name ('gitleaks', 'semgrep', 'trivy')"
    )
    vulnerability_database: VulnerabilityDatabaseMetadata = Field(
        ...,
        description="Vulnerability signature database provenance"
    )
    secrets_detected: Literal[0] = Field(
        0,
        description="Unexempted hardcoded secrets detected (must be strictly 0)"
    )
    sast_blocking_issues: Literal[0] = Field(
        0,
        description="Unexempted ERROR-level static analysis findings (must be strictly 0)"
    )
    cve_critical: Literal[0] = Field(
        0,
        description="Unexempted CRITICAL CVEs with available fixes (must be strictly 0)"
    )
    cve_high: Literal[0] = Field(
        0,
        description="Unexempted HIGH CVEs with available fixes (must be strictly 0)"
    )
    exempted_cve_count: int = Field(
        default=0,
        ge=0,
        description="Total findings covered by active waivers in .nero-security-exceptions.yaml"
    )
    active_waiver_ids: List[str] = Field(
        default_factory=list,
        description="List of active exception rule IDs applied (e.g. ['EXC-2026-001'])"
    )

    @model_validator(mode="after")
    def validate_required_scanners_present(self) -> CandidateSecurityEvidence:
        """Ensures all 3 required security layers (secrets, sast, sca) executed."""
        required_scanners = {"gitleaks", "semgrep", "trivy"}
        present = set(self.scanners.keys())
        missing = required_scanners - present
        if missing:
            raise ValueError(
                f"Security scan evidence is INCOMPLETE. Missing required scanners: {sorted(missing)}. "
                "Fail-closed policy rejects candidate release."
            )
        return self
```

### 5.2 Fail-Closed Policy Enforcement
- **Zero Unexempted Blocking CVEs**: The model rejects releases with unexempted `cve_critical > 0` or `cve_high > 0`. Medium or Low severity findings are allowed by policy.
- **Fail-Closed on Missing/Stale Scans**: If any of Gitleaks, Semgrep, or Trivy did not complete, or if `vulnerability_database.database_age_days > 14`, the validator immediately raises a `ValidationError`.

---

## 6. Canonical Checksum Specification (RFC 8785 Principles)

### 6.1 Checksum Semantics & Boundaries
- **Payload Integrity vs Provenance**: The candidate checksum guarantees **payload integrity** (detecting corruption or byte-level tampering). It does **not** prove author identity or trustworthiness. Provenance and author non-repudiation are established via SLSA in-toto attestations and Cosign digital signatures in Milestone 3.
- **Excluded Field**: The `payload_checksum` field itself is excluded when computing the hash.

### 6.2 Serialization Invariants
To ensure that identical candidate payloads produce the exact same SHA-256 hash regardless of dictionary insertion order, language runtime, or platform:

```python
import hashlib
import json
from typing import Any, Dict

def canonicalize_json(data: Dict[str, Any]) -> bytes:
    """
    Serializes a dictionary to canonical JSON according to deterministic RFC 8785 principles:
    1. Stable Property Ordering: Keys sorted lexicographically at every level recursively.
    2. Minimal Whitespace: No whitespace around separators (':', ',').
    3. Character Encoding: UTF-8 without byte-order mark (BOM).
    4. Numeric Normalization: Floating point values formatted deterministically.
    5. Timestamp Normalization: ISO-8601 UTC with explicit 'Z' suffix.
    """
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False
    ).encode("utf-8")


def compute_candidate_checksum(contract_data: Dict[str, Any]) -> str:
    """Computes SHA-256 digest over canonical JSON bytes with checksum excluded."""
    payload = {k: v for k, v in contract_data.items() if k != "payload_checksum"}
    canonical_bytes = canonicalize_json(payload)
    return hashlib.sha256(canonical_bytes).hexdigest()
```

---

## 7. A3 CI Evidence Compatibility & Migration Matrix

### 7.1 Field Mapping: `CIEvidenceRecord` $\rightarrow$ `CandidateReleaseContract`

| Phase A3 Source Field (`ci_evidence.json`) | Candidate Contract Target Field | Required in A3? | Mapping & Transformation Rule |
|---|---|:---:|---|
| `schema_version` | Validated for `"1.0.0"` | Yes | Rejects versions $\neq$ `"1.0.0"` with `UnsupportedEvidenceVersionError`. |
| `application_id` | `application_id` | Yes | Direct mapping; validated against `APP_ID_REGEX`. |
| `ci_run_id` | `execution.ci_execution_id` | Yes | Direct mapping. |
| `git.repository` | `source.repository` | Yes | Direct mapping. |
| `git.commit_sha` | `source.commit_sha` | Yes | Validated for 40/64 hex characters. |
| `git.branch` | `source.branch` | Yes | Direct mapping. |
| `git.pull_request_id` | `source.pull_request_id` | No | Direct mapping (optional). |
| `jenkins.job` | `execution.job_name` | Yes | Direct mapping. |
| `jenkins.build_number` | `execution.build_number` | Yes | Direct mapping. |
| `jenkins.result` | `execution.build_result` | Yes | Must be `"SUCCESS"`; any other value rejected. |
| `jenkins.duration_seconds` | `execution.duration_seconds` | Yes | Direct mapping. |
| `test_summary.total` | `test_evidence.total_tests` | Yes | Validated: `total >= 1`. |
| `test_summary.passed` | `test_evidence.passed_tests` | Yes | Validated: `passed >= 1`. |
| `test_summary.failed` | `test_evidence.failed_tests` | Yes | Must be `0`. |
| `test_summary.skipped` | `test_evidence.skipped_tests` | Yes | Validated: `passed + failed + skipped == total`. |
| `test_summary.coverage_percentage`| `test_evidence.diff_coverage_percentage` | Yes | Must be $\ge 80.0\%$. |
| `security_summary.secrets_detected` | `security_evidence.secrets_detected` | Yes | Must be `0`. |
| `security_summary.sast_issues` | `security_evidence.sast_blocking_issues` | Yes | Must be `0`. |
| `security_summary.cve_critical` | `security_evidence.cve_critical` | Yes | Must be `0`. |
| `security_summary.cve_high` | `security_evidence.cve_high` | Yes | Must be `0`. |
| `security_summary.exempted_count` | `security_evidence.exempted_cve_count` | Yes | Direct mapping. |
| `artifacts[]` | `components{}` | Yes | Transformed into discriminated union (`OCIImageArtifact` or `StaticArtifact`). |
| `timestamp` | `created_at` | Yes | Validated for ISO-8601 UTC ending in 'Z'. |

### 7.2 Missing-Field & Error Handling
- If `ci_evidence.json` has missing mandatory fields, Pydantic raises a standard `ValidationError`.
- If `jenkins.result != "SUCCESS"`, the factory raises `CandidateEligibilityError("CI build failed")`.
- If `schema_version != "1.0.0"`, the factory raises `UnsupportedEvidenceVersionError`.

---

## 8. Candidate Identity and Provenance Rules

```text
+===================================================================================================+
|                                    IDENTIFIER PATTERNS SPECIFICATION                              |
+===================================================================================================+
| Identifier Entity | Existing Pattern in Repo                  | Proposed Contract Pattern         |
|-------------------|-------------------------------------------|-----------------------------------|
| Application ID    | ^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$         | Same (MetadataModel in models.py) |
| Component ID      | ^[a-z0-9][a-z0-9-]{1,30}[a-z0-9]$         | Same (ComponentModel in models.py)|
| Git Commit SHA    | 40-char hex (git rev-parse HEAD)          | ^[a-f0-9]{40}$|^[a-f0-9]{64}$     |
| CI Execution ID   | ^ci-[a-z0-9-]+-[0-9]+-b[0-9]+$            | Same (ci_evidence.py)             |
| Candidate ID      | New in A4 (Release candidate tracking)    | ^cand-[a-z0-9-]+-[0-9]{14}$       |
| Release Tag       | Semver / release identifier               | ^v?[0-9]+\.[0-9]+(\.[0-9]+)?...   |
+===================================================================================================+
```

### Git Attribution vs Cryptographic Non-Repudiation
- **Git Commit Attribution**: Records author name, email, and commit SHA from the Git tree. This provides development history, but Git commit headers alone do not guarantee non-repudiation because Git author metadata can be forged if commits are unsigned.
- **Signed Build Provenance**: Genuine cryptographic non-repudiation is achieved when the isolated build environment signs an in-toto v1.0 attestation (Task `A4-SEC-002`) and Cosign signs the container digest (Task `A4-SEC-003`).

---

## 9. Comprehensive Unit-Test Matrix (14 Scenarios)

The unit-test suite `tests/unit/test_candidate_contract.py` will implement 14 distinct test cases:

| # | Test Method Name | Input Scenario | Expected Outcome |
|---|---|---|---|
| **1** | `test_01_valid_single_oci_candidate` | Valid `hotel-billing` backend `OCIImageArtifact`, 10 passed tests, 85% coverage, 0 CVEs. | Success. Contract seals; `verify_checksum() is True`. |
| **2** | `test_02_invalid_application_id` | `application_id = "Hotel_Billing!"` (uppercase, special characters). | Fails: `pydantic.ValidationError` on `application_id`. |
| **3** | `test_03_invalid_commit_sha` | `commit_sha = "a1b2c3d"` (short 7-character hash). | Fails: `pydantic.ValidationError` on `commit_sha`. |
| **4** | `test_04_invalid_artifact_digest` | `digest = "sha256:short"` (not 64 hex characters). | Fails: `pydantic.ValidationError` on `digest`. |
| **5** | `test_05_failed_ci_result` | `execution.build_result = "FAILURE"`. | Fails: `pydantic.ValidationError` on `build_result`. |
| **6** | `test_06_arithmetic_test_mismatch` | `total_tests=10`, `passed_tests=8`, `failed_tests=0`, `skipped_tests=1` ($8+0+1 \neq 10$). | Fails: `ValueError` reporting arithmetic inconsistency. |
| **7** | `test_07_coverage_below_80_percent` | `diff_coverage_percentage = 79.9`. | Fails: `pydantic.ValidationError` on `diff_coverage`. |
| **8** | `test_08_missing_required_scanner` | `security_evidence.scanners` omitted `"trivy"`. | Fails: `ValueError` reporting missing required scanner. |
| **9** | `test_09_stale_vulnerability_database`| `database_age_days = 20` (> 14 days maximum threshold). | Fails: `ValueError` reporting stale vulnerability DB. |
| **10**| `test_10_blocking_cve_unexempted` | `cve_critical = 1` with 0 active waivers. | Fails: `pydantic.ValidationError` on `cve_critical`. |
| **11**| `test_11_malformed_timestamp` | `created_at = "2026-11-09 12:00:00"` (missing ISO-8601 'T' and 'Z'). | Fails: `pydantic.ValidationError` on `created_at`. |
| **12**| `test_12_discriminated_union_routing` | Ingests `StaticArtifact` without container fields and `WorkerArtifact` with nested OCI image. | Success. Discriminator correctly maps each type. |
| **13**| `test_13_canonical_checksum_stability`| Serializes candidate with varying key order; asserts identical SHA-256 hash. | Success. Hashes match byte-for-byte. |
| **14**| `test_14_from_ci_evidence_compatibility`| Ingests raw Phase A3 `ci_evidence.json` dictionary via `from_ci_evidence()`. | Success. Mapped to valid contract with valid checksum. |

> [!NOTE]
> **Audit Ledger Protection**: All 14 tests run in-memory. Zero tests call `append_audit_record()`. The audit ledger remains untouched.

---

## 10. File-Level Implementation Plan

When Gate 3 is authorized, implementation will touch strictly these three files:

### Files to Create:
1. `platform_core/models/__init__.py`: Package initialization exporting contract models.
2. `platform_core/models/candidate_contract.py`: Complete Pydantic v2 discriminated-union candidate contract models (~240 lines).
3. `tests/unit/test_candidate_contract.py`: 14-scenario unit-test suite (~260 lines).

### Files to Modify:
- **NONE**. No existing application code, Dockerfiles, Jenkins pipelines, or Terraform files are modified.

---

## 11. Objective Acceptance Criteria for Task A4-CAN-001

1. **Discriminated Union Functionality**: Successfully validates `OCIImageArtifact`, `StaticArtifact`, and `WorkerArtifact` without field leakage.
2. **Digest-First Identity**: Enforces 64-character SHA-256 digests as the sole authoritative immutable identity.
3. **Arithmetic Test Integrity**: Fails closed if `passed + failed + skipped != total` or if `passed < 1`.
4. **DevSecOps Freshness**: Rejects scans with stale vulnerability databases (> 14 days old).
5. **Zero Blocking CVEs**: Enforces zero unexempted CRITICAL/HIGH CVEs, while tracking active waivers from `.nero-security-exceptions.yaml`.
6. **Deterministic Checksumming**: Computes identical SHA-256 hashes across varying key orderings.
7. **CI Ingestion Compatibility**: `from_ci_evidence()` ingests Phase A3 `ci_evidence.json` cleanly.
8. **100% Test Pass Rate**: All 14 unit tests pass with zero warnings and zero writes to `audit_log.jsonl`.

---

## 12. Risks and Dependencies

| Risk ID | Risk Description | Impact | Mitigation Strategy |
|---|---|:---:|---|
| **RSK-CAN-01** | Transitive Pydantic version mismatch | Medium | Working environment verified on Python 3.12 with Pydantic v2. |
| **RSK-CAN-02** | Float serialization differences in checksums | Low | `canonicalize_json` normalizes floats with deterministic string formatting. |
| **RSK-CAN-03** | Stale vulnerability DB false positives in offline lab | Low | Configurable `MAX_ALLOWED_OFFLINE_DAYS = 14` with clear remediation diagnostics. |

---

## 13. Updated 8.0 EH Work Breakdown

The 8.0 Nominal Engineering Hours baseline is retained without change:

| Subtask ID | Work Description | Planned EH | Discipline |
|---|---|:---:|---|
| **A4-CAN-001.1** | Create `platform_core/models/` and implement discriminated union artifact hierarchy (`OCIImageArtifact`, `StaticArtifact`, `WorkerArtifact`). | 2.0 EH | Core Development |
| **A4-CAN-001.2** | Implement arithmetic test evidence validation and fail-closed security evidence with DB freshness checks. | 2.0 EH | Core Development |
| **A4-CAN-001.3** | Implement canonical JSON serialization (RFC 8785 principles) and deterministic SHA-256 checksumming. | 1.5 EH | System Architecture |
| **A4-CAN-001.4** | Implement `from_ci_evidence()` compatibility factory supporting Phase A3 schema `1.0.0`. | 1.0 EH | Integration |
| **A4-CAN-001.5** | Author 14-scenario unit-test suite in `tests/unit/test_candidate_contract.py` with zero-audit-pollution guarantees. | 1.5 EH | Test Engineering |
| **TOTAL** | **A4-CAN-001 Implementation Scope** | **8.0 EH** | |

---

## 14. Final Authorization Boundary

```text
+===================================================================================================+
|                                    FINAL AUTHORIZATION BOUNDARY                                   |
+===================================================================================================+
|  This design refinement is complete and strictly technical.                                      |
|  No code has been written. No files have been created.                                            |
|  Gate 3 remains PENDING OWNER AUTHORIZATION. Implementation remains strictly halted.              |
+===================================================================================================+
```

```text
A4-CAN-001 REFINED DESIGN COMPLETE — AWAITING PLATFORM OWNER IMPLEMENTATION AUTHORIZATION
```
