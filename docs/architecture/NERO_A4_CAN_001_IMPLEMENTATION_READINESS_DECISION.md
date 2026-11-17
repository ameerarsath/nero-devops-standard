# NERO Programme 1 — Phase A4
# Task Implementation Readiness Decision: A4-CAN-001
## Candidate Release Contract Model (`platform_core/models/candidate_contract.py`)

**Document ID:** NERO-A4-CAN-001-DECISION-001  
**Task ID:** `A4-CAN-001`  
**Estimated Effort:** 8.0 Engineering Hours (Nominal Baseline Maintained)  
**Governing Milestone:** Milestone 1 — Candidate Ingestion & Release Manifest Architecture (30.0 EH)  
**Date:** November 9, 2026  
**Author:** Principal Platform Architect & Senior Python Engineer  
**Operating Mode:** STRICTLY READ-ONLY ARCHITECTURAL DECISION (Zero Implementation Code Written)  
**Target Repository:** `D:\project\billing-system-master\billing-system-master`  
**Active Git Branch:** `devops/jenkins-floci-local-lab`  

---

## 1. Executive Summary & Governance Status

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

### 1.2 Objective of This Report
This report resolves the final three architectural and policy ambiguities in **Task A4-CAN-001** before implementation authorization:
1. **Skipped-Test Qualification Rule**: Codifies the conservative rule consistent with existing empirical evidence.
2. **RFC 8785 JCS Implementation Strategy**: Evaluates dependency availability in the offline lab and specifies an in-tree canonicalization architecture.
3. **Worker Artifact Execution Compatibility**: Evaluates the ECS deployment adapter and application specifications to align the worker model with actual platform capabilities (eliminating fictional static-tarball worker execution).

---

## 2. Skipped-Test Qualification Policy Resolution

### 2.1 Repository Inspection & Fact Finding
- **JUnit Parser Logic (`[VERIFIED]`)**: In [`platform_core/engine/junit_aggregator.py`](file:///d:/project/billing-system-master/billing-system-master/platform_core/engine/junit_aggregator.py#L30-L36), `AggregatedTestReport` parses `<skipped>` XML tags. The test suite status is defined as:
  ```python
  report.success = (report.failed == 0 and report.errors == 0)
  ```
  In the raw A3 aggregator, non-zero skipped tests do not trigger `report.success = False`.
- **Empirical Qualification Baseline (`[VERIFIED]`)**: In all verified historical qualification records across A1, A2, and A3 (including the 139 tests under `tests/` and 153 tests repository-wide), **the skipped count was exactly zero** (`0 failed, 0 skipped`).
- **Policy Rule Evaluation**:
  - **Rule A (Strict Qualification — Recommended)**:
    ```python
    failed_tests == 0 and skipped_tests == 0 and passed_tests == total_tests and passed_tests >= 1
    ```
    Every declared test must execute and pass. Zero tests may be skipped.
  - **Rule B (Conditional Qualification)**:
    ```python
    failed_tests == 0 and passed_tests >= 1 and skipped_tests >= 0 and (passed_tests + skipped_tests == total_tests)
    ```
    Skipped tests are permitted only under an explicitly approved policy with documented annotations (e.g. `@pytest.mark.skipif`), while diff coverage must remain $\ge 80.0\%$.

### 2.2 Recommendation for Task A4-CAN-001
- **Recommendation (`[EXISTING POLICY]`)**: Adopt **Rule A (Strict Qualification: zero failed, zero skipped)** as the default validation baseline for `CandidateReleaseContract`.
- **Rationale**: Rule A is 100% consistent with all verified qualification evidence in the repository. Introducing a non-zero skipped-test allowance without owner approval would weaken the qualification gate.
- **Owner Decision Boundary (`[REQUIRES OWNER APPROVAL]`)**: If the Platform Owner intends to permit conditional skips (e.g. for operating-system-specific integration tests), an explicit decision must be recorded under `DEC-A4-02`.

---

## 3. RFC 8785 Implementation Selection & Assessment

### 3.1 Dependency Inspection in Active Environment
A direct inspection of the active Python environment was performed `[VERIFIED]`:
- `python -m pip list` confirmed that:
  - `rfc8785` is **NOT installed** `[VERIFIED]`.
  - `canonicaljson` is **NOT installed** `[VERIFIED]`.
  - `jcs` is **NOT installed** `[VERIFIED]`.
- Operating Constraint: Installing new external packages via `pip` or modifying requirements files is strictly prohibited during preflight `[VERIFIED]`.

### 3.2 Evaluation of Candidate Approaches

| Approach | Standards Conformance | Offline Availability | License Impact | Architecture Assessment |
|---|:---:|:---:|:---:|---|
| **External Package (`rfc8785`)** | Full RFC 8785 (Cyberphone ref) | ❌ Not installed in lab | Apache 2.0 | Prohibited: Cannot install dependencies in offline lab. |
| **External Package (`canonicaljson`)** | ❌ Non-conforming (Matrix JCS) | ❌ Not installed in lab | Apache 2.0 | Prohibited: Lacks RFC 8785 float/UTF-16 rules. |
| **Standard Library (`json.dumps(sort_keys=True)`)** | ❌ Non-conforming (Unicode code-point sort, Python float format) | ✅ Built-in | Python Software Foundation | Incomplete: Fails RFC 8785 on surrogate pairs and floats. |
| **In-Tree Pure-Python RFC 8785 Module (`platform_core/models/canonical_json.py`)** | ✅ Full RFC 8785 | ✅ Zero external dependencies | Internal / Apache 2.0 compatible | **RECOMMENDED**: Self-contained, offline-ready, conforming. |

### 3.3 Recommended Architectural Strategy
Task `A4-CAN-001` will deliver an in-tree canonicalization module:
```text
platform_core/models/canonical_json.py
```
- **Technical Standards**:
  1. Lexicographical key sorting by UTF-16 code units (RFC 8785 Section 3.2.3).
  2. Number serialization conforming to ECMAScript 6 / IEEE 754 (RFC 8785 Section 3.2.2.3).
  3. Rejection of `NaN`, `Infinity`, and `-Infinity` (RFC 8785 Section 3.2.2.3).
  4. String escaping per RFC 8785 Section 3.2.2.2 (no solidus `/` escaping).
  5. UTF-8 byte stream output without BOM.
  6. Verification against official RFC 8785 test vectors in `tests/unit/test_candidate_contract.py`.
- **Integrity vs Authenticity Boundary (`[VERIFIED]`)**: The SHA-256 payload checksum guarantees **payload integrity** (tamper detection). It does **not** prove author identity or trustworthiness (which is provided by Cosign signatures in Milestone 3).

---

## 4. Worker Execution Compatibility Findings

### 4.1 Deployment Adapter & Catalog Inspection
A thorough inspection of deployment modules was conducted:
1. **`ECSDeploymentAdapter` (`[VERIFIED]`)**: In [`platform_core/adapters/deployment/ecs_adapter.py`](file:///d:/project/billing-system-master/billing-system-master/platform_core/adapters/deployment/ecs_adapter.py#L87-L105), components are deployed via Docker/ECS:
   ```python
   cmd = ["docker", "run", "-d", "--name", c_name, "--network", network_name, "--restart", "unless-stopped"]
   cmd.append(image_ref)
   ```
   The adapter requires a container image reference (`image_ref`).
2. **`DeploymentManager` (`[VERIFIED]`)**: In [`platform_core/engine/deployment_manager.py`](file:///d:/project/billing-system-master/billing-system-master/platform_core/engine/deployment_manager.py#L241):
   ```python
   container_comps = [c for c in app_spec.spec.components if c.type in ("container-service", "worker-service", "worker")]
   ```
   Workers are explicitly categorized as container workloads.
3. **Reference Application Specification (`[VERIFIED]`)**: In [`applications/sample-python-worker/app.spec.yaml`](file:///d:/project/billing-system-master/billing-system-master/applications/sample-python-worker/app.spec.yaml#L11-L36), the worker is declared as:
   ```yaml
   components:
     - name: worker
       type: container-service
       build:
         adapter: "dockerfile"
       deployment:
         adapter: "ecs"
   ```
4. **`S3FrontendDeploymentAdapter` (`[VERIFIED]`)**: In [`platform_core/adapters/deployment/s3_adapter.py`](file:///d:/project/billing-system-master/billing-system-master/platform_core/adapters/deployment/s3_adapter.py#L38-L60), static deployment is strictly designed for web frontend directories (`dist_dir` containing HTML, JS, CSS, PNG).

### 4.2 Structural Distinction & Correction
```text
+---------------------------------------------------------------------------------------------------+
|                                 PLATFORM WORKLOAD REALITY MATRIX                                  |
+---------------------------------------------------------------------------------------------------+
| Workload Type      | Execution Mode | Packaging Mechanism | Storage Location | Supported in NERO? |
|--------------------|----------------|---------------------|------------------|--------------------|
| OCI Container App  | Container (ECS)| Dockerfile / Build  | OCI Registry     | YES (Verified)     |
| OCI Worker App     | Container (ECS)| Dockerfile / Build  | OCI Registry     | YES (Verified)     |
| Static Web App     | Static Asset   | Vite / Webpack Tar  | Floci S3 Bucket  | YES (Verified)     |
| Process Worker     | Host Process   | Raw Tarball / Script| Floci S3 Bucket  | NO (Non-existent)  |
+---------------------------------------------------------------------------------------------------+
```

- **Architectural Reality (`[VERIFIED]`)**: **Process workers running directly from static tarballs on S3 DO NOT EXIST in the NERO platform architecture.**
- **Model Correction (`[EXISTING POLICY]`)**: The candidate release model must **not** invent support for running process workers from static tarballs. In `A4-CAN-001`, all workers are modeled as containerized workloads referencing an `OCIImageArtifact` with an immutable SHA-256 digest:
  ```python
  class WorkerArtifact(BaseComponentArtifact):
      type: Literal["worker"] = "worker"
      image: OCIImageArtifact = Field(..., description="Container image defining worker executable")
      worker_queue: Optional[str] = Field(default=None, description="Target SQS or Celery queue")
  ```

---

## 5. Final Candidate Contract Requirements & Invariants

The `CandidateReleaseContract` model enforces the following twelve confirmed invariants:

```text
+===================================================================================================+
|                                  CONFIRMED CONTRACT INVARIANTS                                    |
+===================================================================================================+
```

1. **Immutable Container Image Digests (`[EXISTING POLICY]`)**: All OCI container images must reference an immutable 64-character SHA-256 digest (`sha256:[a-f0-9]{64}`). Tags are optional, non-authoritative metadata.
2. **Downloaded-Byte Checksum for Static Assets (`[EXISTING POLICY]`)**: Static artifacts in S3 are identified by their SHA-256 content hash. S3 keys are mutable storage locators; the checksum is the authoritative identity.
3. **Container-Only Worker Semantics (`[EXISTING POLICY]`)**: Workers execute strictly as container workloads referencing `OCIImageArtifact`. Fictional static-tarball worker execution is rejected.
4. **Strict Arithmetic Test Consistency (`[EXISTING POLICY]`)**: Enforces `passed_tests + failed_tests + skipped_tests == total_tests`.
5. **Strict Test Qualification Rule (`[EXISTING POLICY]`)**: Enforces `failed_tests == 0`, `skipped_tests == 0`, `passed_tests >= 1`, and `diff_coverage_percentage >= 80.0%`.
6. **Per-Scanner Target Specialization (`[EXISTING POLICY]`)**: Telemetry binds Gitleaks to Git commit SHA, Semgrep to source tree and ruleset, and Trivy to the exact 64-character OCI image digest or lockfile checksum.
7. **Fail-Closed Security Posture (`[EXISTING POLICY]`)**: Any missing required scanner or scanner execution status $\neq$ `"COMPLETED"` immediately fails candidate qualification.
8. **Separation of DB Verification vs Freshness (`[VERIFIED]`)**: Cryptographic integrity of the offline database is strictly separated from elapsed publication time.
9. **Proposed 14-Day Limit Kept Unapproved (`[PROPOSED — REQUIRES OWNER APPROVAL]`)**: The 14-day freshness threshold is tracked as a proposal and will not silently fail builds without owner approval.
10. **Deterministic RFC 8785 Serialization (`[PROPOSED]`)**: Canonical payload serialization uses UTF-16 code-unit key sorting and ECMAScript number normalization with `payload_checksum` excluded.
11. **Integrity vs Authenticity Boundary (`[VERIFIED]`)**: The SHA-256 checksum proves payload integrity, not author identity.
12. **Zero External Side Effects (`[VERIFIED]`)**: Model instantiation and validation is 100% in-memory; zero calls to Jenkins, Docker, Floci, AWS, or the authoritative audit ledger.

---

## 6. Exact Implementation File Scope

When the Platform Owner authorizes Gate 3, implementation of `A4-CAN-001` will touch strictly the following files:

### Files to Create:
1. `platform_core/models/__init__.py`: Package initialization exporting public models (~15 lines).
2. `platform_core/models/canonical_json.py`: Standards-conforming RFC 8785 JCS canonicalizer (~85 lines).
3. `platform_core/models/candidate_contract.py`: Pydantic v2 candidate contract models and validation logic (~260 lines).
4. `tests/unit/test_candidate_contract.py`: Comprehensive 14-scenario unit-test suite (~280 lines).

### Files to Modify:
- **NONE** `[VERIFIED]`. Zero modifications to existing application code, pipelines, Dockerfiles, Terraform scripts, or audit files.

---

## 7. Final 8.0 EH Work Breakdown

The 8.0 Nominal Engineering Hours baseline for `A4-CAN-001` is partitioned as follows:

| Subtask ID | Work Description | Planned EH | Discipline |
|---|---|:---:|---|
| **A4-CAN-001.1** | Create `platform_core/models/` package and implement `canonical_json.py` conforming to RFC 8785 with test vectors. | 1.5 EH | Core Architecture |
| **A4-CAN-001.2** | Implement discriminated artifact hierarchy (`OCIImageArtifact`, `StaticArtifact`, `WorkerArtifact`) enforcing container worker semantics. | 1.5 EH | Python Core Dev |
| **A4-CAN-001.3** | Implement strict arithmetic test evidence validation and per-scanner security evidence with fail-closed rules. | 2.0 EH | DevSecOps Engineering |
| **A4-CAN-001.4** | Implement root `CandidateReleaseContract` with checksum sealing and `from_ci_evidence()` A3 compatibility adapter. | 1.5 EH | Pipeline Integration |
| **A4-CAN-001.5** | Author 14-scenario unit-test suite in `tests/unit/test_candidate_contract.py` with zero-audit-pollution guarantees. | 1.5 EH | Test Engineering |
| **TOTAL** | **A4-CAN-001 Implementation Scope** | **8.0 EH** | |

---

## 8. Test Acceptance Criteria

Task `A4-CAN-001` will be considered complete when:
1. `CandidateReleaseContract` validates valid candidate structures for all 4 reference applications.
2. Incompatible or invalid candidates are rejected deterministically with explicit `ValidationError` messages.
3. In-tree RFC 8785 canonicalizer passes official JCS test vectors.
4. Process workers attempting to execute static tarballs are rejected as unsupported.
5. All 14 test cases in `tests/unit/test_candidate_contract.py` pass with 100% success (0 failed, 0 skipped).
6. Unit tests execute in memory with zero writes to `platform_core/audit/audit_log.jsonl`.
7. Existing A1–A3 test suites remain 100% unaffected.
8. The 188.0 EH Phase A4 baseline remains unaltered.

---

## 9. Implementation Risk & Recovery Plan

| Risk Description | Probability | Impact | Mitigation Strategy | Rollback Action |
|---|:---:|:---:|---|---|
| **Pydantic v2 Version Drift** | Low | High | Environment verified on Pydantic 2.13.4. Models use standard ConfigDict. | Delete new model files. |
| **RFC 8785 Float Edge-Cases** | Low | Medium | JCS module includes unit tests covering integer-floats, exponents, and edge cases. | Fall back to standard canonicalizer. |
| **Audit Ledger Pollution** | Low | Critical | Unit tests instantiate models in memory; no logger imports or file writes. | Inviolable: audit file is never opened. |

---

## 10. Outstanding Platform Owner Decisions

| Decision ID | Policy Topic | Recommended Conservative Baseline | Alternative Option | Impact |
|---|---|---|---|---|
| **DEC-A4-01** | Vulnerability DB Freshness | Track DB age as informational; do not enforce 14-day limit without owner approval `[RECOMMENDED]`. | Enforce strict `database_age_days <= 14`. | Alternative option may fail builds during extended offline lab cycles. |
| **DEC-A4-02** | Skipped-Test Policy | Enforce strict `skipped_tests == 0` matching empirical A1–A3 evidence `[RECOMMENDED]`. | Permit conditional skips (`skipped_tests >= 0`) with documented justification. | Alternative option requires ongoing governance tracking of skip rationales. |

---

## 11. Final Authorization Boundary

```text
+===================================================================================================+
|                                    FINAL AUTHORIZATION BOUNDARY                                   |
+===================================================================================================+
|  This implementation readiness decision is complete and authoritative.                           |
|  No code has been written. No files have been created.                                            |
|  Gate 3 remains PENDING OWNER AUTHORIZATION. Implementation remains strictly halted.              |
+===================================================================================================+
```

```text
A4-CAN-001 IMPLEMENTATION DESIGN READY — AWAITING EXPLICIT OWNER AUTHORIZATION
```
