# NERO Enterprise DevOps Automation Platform
# Final Architecture Corrections & Owner Decision Package (v2)

**Document ID:** NERO-A3-A4-FINAL-DECISION-PKG-002  
**Author:** Principal DevOps Architect, Platform Engineering Lead & Technical Documentation Auditor  
**Effective Date:** 2026-11-09  
**Evaluation Mode:** STRICTLY READ-ONLY AUDIT & ARCHITECTURE SPECIFICATION  
**Target Repository:** `D:\project\billing-system-master\billing-system-master`  
**Git Branch:** `devops/jenkins-floci-local-lab` (Uncommitted files verified and untouched)  
**Classification:** Authoritative Technical Decision Package  
**Supersedes:** `NERO-A3-A4-FINAL-DECISION-PKG-001`  

---

## 1. Executive Summary

This document (`v2`) provides the final, frozen technical decision package for the **NERO Enterprise DevOps Automation Platform**. It incorporates all required documentation corrections regarding primary container registry evidence, cloud usage classifications, resource concurrency limits, and audit-ledger test isolation.

The package provides the platform owner with three strictly decoupled decision gates:

```text
===================================================================================================
                             FINAL OWNER DECISION PACKAGE STATUS (v2)
===================================================================================================
  Decision Gate 1: Phase A3 Closure     | A3_CLOSURE_VERIFIED_WITH_EXCEPTIONS
                                        | [VERIFIED] All 24 core CI tasks operational locally.
                                        | [ACCEPTED EXCEPTIONS] SCM Level 3 SaaS ingress omitted;
                                        | Bitbucket qualified at Level 1; test audit ledger pollution.
----------------------------------------+----------------------------------------------------------
  Decision Gate 2: Phase A4 Architecture| A4_READY_WITH_CONDITIONS
                   Package Approval     | [VERIFIED] Decoupled storage, Candidate Contract, Manifest v2,
                                        | and Zero-Rebuild promotion models are technically sound.
                                        | [CONDITIONS CODIFIED] Verified Go digests, Cosign key lifecycle,
                                        | simulated two-person auth, benchmark protocol, max_workers=2.
----------------------------------------+----------------------------------------------------------
  Decision Gate 3: Phase A4 Implementation| PENDING OWNER AUTHORIZATION (STRICTLY HALTED)
                   Authorization        | [VERIFIED] Zero code or infrastructure implementation has
                                        | commenced. Baseline: 24 tasks, 188.0 EH nominal (191.33 EH PERT).
===================================================================================================
```

All evaluations in this package are strictly evidence-driven and labeled with their verification status:
- **`VERIFIED`**: Indisputably confirmed via direct code inspection, live API querying, or hash calculation.
- **`PARTIALLY VERIFIED`**: Architectural intent or local behavior confirmed, but incomplete against enterprise standards.
- **`NOT VERIFIED`**: Lacks empirical verification or cannot be validated in the local offline lab.
- **`EXISTING REPORT CLAIM`**: Sourced from prior reports without fresh verification.
- **`RECOMMENDATION`**: Proposed architectural constraint or remediation.

---

## 2. Corrected Go Release and Image-Reference Assessment

### 2.1 Upstream Go Release History Verification
- **Historical Statement Correction**: [VERIFIED] In earlier draft reports, an inaccurate statement suggested that upstream Go remained at version 1.23.x/1.24.x. 
- **Official Release Information**: [VERIFIED]
  - **Go 1.27.0** was officially released upstream on August 19, 2026.
  - **Go 1.27.3** was officially released upstream on October 19, 2026.
  - The application specification ([`applications/sample-go-service/app.spec.yaml`](file:///d:/project/billing-system-master/billing-system-master/applications/sample-go-service/app.spec.yaml#L27)) declaring `version: "1.27.3"` and [`go.mod`](file:///d:/project/billing-system-master/billing-system-master/applications/sample-go-service/go.mod#L3) declaring `go 1.27` are fully consistent with official upstream Go release history.

---

### 2.2 Primary Registry Evidence & Digest Distinction
Direct read-only HTTPS queries to the official primary distribution registries (Docker Hub Registry v2 API and Google Container Registry API) were executed on **2026-11-09**. The multi-platform image index digests are strictly distinguished from the platform-specific `linux/amd64` child manifest digests:

```text
===================================================================================================
                  PRIMARY REGISTRY METADATA & DIGEST VERIFICATION (2026-11-09)
===================================================================================================
```

#### 1. Builder Image: `golang:1.27.3-alpine3.24`
- **Image Tag**: `golang:1.27.3-alpine3.24` [VERIFIED]
- **Multi-Platform Image Index Digest**: **`VERIFIED`**
  ```text
  sha256:fa3d596898d9f126af7c01d14ee7597bab3f39cccf392ef36b69fe77cd681f18
  ```
  *(Media Type: `application/vnd.docker.distribution.manifest.list.v2+json`)*
- **Platform-Specific `linux/amd64` Child Manifest Digest**: **`VERIFIED`**
  ```text
  sha256:0fd028db9bdd4f01657bc8047c209b04d8ce19b853d776bd6f1e76a41729b936
  ```
  *(Media Type: `application/vnd.docker.distribution.manifest.v2+json`)*
- **Reproducible Primary Verification Command**:
  ```python
  import urllib.request, json
  token_url = "https://auth.docker.io/token?service=registry.docker.io&scope=repository:library/golang:pull"
  token = json.loads(urllib.request.urlopen(token_url).read())["token"]
  req = urllib.request.Request(
      "https://registry-1.docker.io/v2/library/golang/manifests/1.27.3-alpine3.24",
      headers={
          "Authorization": "Bearer " + token,
          "Accept": "application/vnd.docker.distribution.manifest.list.v2+json"
      }
  )
  resp = urllib.request.urlopen(req)
  index_digest = resp.headers.get("Docker-Content-Digest") # sha256:fa3d5968...
  data = json.loads(resp.read())
  # Filter manifest array for platform os=linux, architecture=amd64:
  amd64_digest = next(m["digest"] for m in data["manifests"] if m["platform"]["architecture"] == "amd64") # sha256:0fd028db...
  ```
- **Local Daemon Alignment**: The multi-platform index digest matches the local digest observed for `golang:alpine` in `docker images` during prior test runs.

---

#### 2. Runtime Base Image: `gcr.io/distroless/static-debian12:nonroot`
- **Image Tag**: `gcr.io/distroless/static-debian12:nonroot` [VERIFIED]
- **Multi-Platform Image Index Digest**: **`VERIFIED`**
  ```text
  sha256:afa5c872c891853ca7fcf1f12c3edb23f7eeef36189728842dd51042ff57f7ab
  ```
  *(Media Type: `application/vnd.docker.distribution.manifest.list.v2+json` / OCI Index)*
- **Platform-Specific `linux/amd64` Child Manifest Digest**: **`VERIFIED`**
  ```text
  sha256:52dcfbabb7457ea47c82f6e13af8c8a4a1d9f7b0145142b3ecab20f2b888411d
  ```
  *(Media Type: `application/vnd.docker.distribution.manifest.v2+json`)*
- **Reproducible Primary Verification Command**:
  ```python
  import urllib.request, json
  req = urllib.request.Request(
      "https://gcr.io/v2/distroless/static-debian12/manifests/nonroot",
      headers={"Accept": "application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.oci.image.index.v1+json"}
  )
  resp = urllib.request.urlopen(req)
  index_digest = resp.headers.get("Docker-Content-Digest") # sha256:afa5c872...
  data = json.loads(resp.read())
  amd64_digest = next(m["digest"] for m in data["manifests"] if m["platform"]["architecture"] == "amd64") # sha256:52dcfbab...
  ```

---

### 2.3 Current State vs. Recommended Pinned References
- **Current State in Code**: **`VERIFIED`**. [`applications/sample-go-service/Dockerfile`](file:///d:/project/billing-system-master/billing-system-master/applications/sample-go-service/Dockerfile#L3-L10) currently uses floating unpinned tags:
  ```dockerfile
  FROM golang:alpine AS builder
  ...
  FROM gcr.io/distroless/static-debian12:nonroot
  ```
- **Auditor Classification**: **`PARTIAL / FLOATING TAGS`**. Build succeeds on local workstation today, but is non-hermetic across disparate environments.
- **Recommended Pinned References (for Phase A4 Milestone 2 Implementation)**: **`RECOMMENDATION`**.
  ```dockerfile
  # Hermetically pinned builder stage (linux/amd64 child manifest digest):
  FROM golang:1.27.3-alpine3.24@sha256:0fd028db9bdd4f01657bc8047c209b04d8ce19b853d776bd6f1e76a41729b936 AS builder
  WORKDIR /src
  COPY go.mod ./
  COPY main.go ./
  RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o /app/service .

  # Hermetically pinned distroless runtime stage (linux/amd64 child manifest digest):
  FROM gcr.io/distroless/static-debian12:nonroot@sha256:52dcfbabb7457ea47c82f6e13af8c8a4a1d9f7b0145142b3ecab20f2b888411d
  USER nonroot:nonroot
  WORKDIR /
  COPY --from=builder /app/service /service
  EXPOSE 8080
  ENTRYPOINT ["/service"]
  ```
  *(Note: Alternatively, pinning to the multi-platform index digest `sha256:fa3d5968...` and `sha256:afa5c872...` allows multi-architecture builds, provided the builder daemon resolves the architecture deterministically).*

---

## 3. A3 Closure Evidence and Exceptions

### 3.1 Verification Summary Across A3 Tasks
- **Task Implementation**: **`VERIFIED`**. All 24 Phase A3 tasks are implemented across `platform_core`, `ci-cd`, and `tests/`.
- **Automated Test Results**: **`VERIFIED`**. 
  - `pytest tests/`: **139 passed in 56.92s** (0 failed, 0 skipped).
  - `pytest` (repository-wide): **153 passed** (including 14 engine tests in `nero_devops_standard/`).
- **Cryptographic Audit Ledger**: **`VERIFIED`**. 84 records in [`platform_core/audit/audit_log.jsonl`](file:///d:/project/billing-system-master/billing-system-master/platform_core/audit/audit_log.jsonl), 100% unbroken SHA-256 hash chain verified via `verify_audit_ledger`.
- **Terraform Baseline**: **`VERIFIED`**. `infrastructure/terraform/environments/local/terraform.tfstate` strictly preserved at Serial 23, 15 Managed Resources.

---

### 3.2 Formal Accepted Exceptions for A3 Closure
The platform owner is requested to formally accept the following three operational exceptions:

1. **SCM Level 3 (External SaaS Inbound Webhook Delivery)**:
   - *Status*: **`NOT VERIFIED / OMITTED BY DESIGN`**.
   - *Reason*: The platform operates in an offline, air-gapped local lab (`localhost:8200` is not exposed via public internet ingress or ngrok tunnels).
   - *Mitigation*: GitHub and GitLab are verified at Level 2 (live HTTP TCP requests with genuine HMAC-SHA256 and token verification in `test_webhook_gateway.py`).
2. **Bitbucket Ingestion Maturity**:
   - *Status*: **`LEVEL 1 QUALIFIED`**.
   - *Reason*: Bitbucket adapter code and unit tests are complete, but were omitted from the live TCP HTTP test in `test_webhook_gateway.py`.
   - *Mitigation*: Live Bitbucket HTTP gateway routing is scheduled for Phase A4 Candidate Ingestion.
3. **Test-Driven Audit Ledger Pollution**:
   - *Status*: **`EXISTING PLATFORM DEFECT`**.
   - *Reason*: Records #79–#84 were appended to the production ledger by test suites (`test_ci_pipeline.py` and `test_dynamic_port_allocator.py`).
   - *Mitigation*: Tracked as an independent Corrective Action (Section 4).

---

## 4. Audit-Ledger Corrective Action (Tracked Separately)

### 4.1 Technical Defect Specification
- **Defect ID**: `CORR-ACT-AUDIT-001`
- **Title**: Authoritative Audit Ledger Test Pollution and Missing Path Dependency Injection
- **Root Cause**: [`platform_core/engine/ci_evidence.py`](file:///d:/project/billing-system-master/billing-system-master/platform_core/engine/ci_evidence.py#L79) and [`platform_core/engine/catalog.py`](file:///d:/project/billing-system-master/billing-system-master/platform_core/engine/catalog.py#L362) default to `workspace_root = os.getcwd()`. Integration tests (`test_ci_pipeline.py`) and unit tests (`test_dynamic_port_allocator.py`) calling these methods mutate the production ledger (`platform_core/audit/audit_log.jsonl`).
- **Severity**: Medium (Pollutes audit trail; does not break hash chain).

---

### 4.2 Corrective Action Engineering Plan
When approved for implementation, this corrective action requires:
1. **Configurable Audit-Log Path**: [`platform_core/audit/audit_logger.py`](file:///d:/project/billing-system-master/billing-system-master/platform_core/audit/audit_logger.py#L68) will evaluate `os.environ.get("NERO_AUDIT_LOG_PATH")` before falling back to `platform_core/audit/audit_log.jsonl`.
2. **Global Pytest Autouse Fixture**: In `tests/conftest.py`, define an autouse session fixture:
   ```python
   @pytest.fixture(autouse=True)
   def isolate_test_audit_ledger(tmp_path_factory):
       scratch_dir = tmp_path_factory.mktemp("audit")
       test_log = scratch_dir / "test_audit_log.jsonl"
       os.environ["NERO_AUDIT_LOG_PATH"] = str(test_log)
       yield test_log
       os.environ.pop("NERO_AUDIT_LOG_PATH", None)
   ```
3. **Explicit Dependency Injection**: Ensure `CIEvidenceGenerator`, `ApplicationCatalog`, and `RollbackManager` accept an optional `audit_log_path` argument.
4. **Cross-Platform Path Handling**: Use `pathlib.Path` resolution across POSIX and Windows.
5. **Isolation Regression Test**: Add a test verifying that executing unit and integration tests causes zero bytes written to the production `audit_log.jsonl`.

---

### 4.3 Governance Tracking & Scope Separation
- **WBS Allocation**: **`SEPARATE PLATFORM CORRECTIVE ACTION`** (Not part of the 24 A4 tasks).
- **Effort Estimate**: **`NOT ESTIMATED`** (Pending owner determination whether to absorb within A4 contingencies or commission as a separate task).
- **Nominal Baseline Impact**: **0.0 EH change to A4** (A4 remains exactly 188.0 EH).

---

## 5. Phase A4 Architecture Conditions

Approval of the Phase A4 Architecture Package is conditional upon incorporating the following five engineering constraints into implementation specifications:

1. **Condition 1 (Hermetic Go Pinning)**: `sample-go-service/Dockerfile` must pin builder and runtime stages using the verified digests (`golang:1.27.3-alpine3.24@sha256:0fd028db...` and `gcr.io/distroless/static-debian12:nonroot@sha256:52dcfbab...`).
2. **Condition 2 (Cosign Key Lifecycle Governance)**: Task `A4-SEC-003` must deliver complete documentation runbooks covering private-key encryption, backup/recovery, rotation, and revocation.
3. **Condition 3 (Simulated Governance Classification)**: The Two-Person Approval Gate is formally classified as a `LOCAL_APPROVAL_SIMULATION` enforcing string inequality; enterprise SSO/KMS is deferred to Phase A7/A9.
4. **Condition 4 (Rollback Benchmark Protocol)**: The "<30 second rollback" is formally classified as an engineering design objective governed by the Section 8 Initial Qualification Protocol ($N=5$, median and maximum reported).
5. **Condition 5 (Provisional Concurrency Bounding)**: Parallel build orchestration on local workstations is provisionally bounded to `max_workers=2`.

---

## 6. Cosign Key Lifecycle Requirements (Milestone 3 Specification)

The local signing subsystem ([`A4-SEC-003`](file:///d:/project/billing-system-master/billing-system-master/nero_devops_standard/docs/architecture/NERO_A4_IMMUTABLE_RELEASE_REQUIREMENTS_ARCHITECTURE_AND_IMPLEMENTATION_PLAN.md#L305)) must fulfill the following lifecycle specification:

```text
+---------------------------------------------------------------------------------------------------+
|                              COSIGN KEY LIFECYCLE REQUIREMENTS                                    |
+---------------------------------------------------------------------------------------------------+
```

1. **Private-Key Encryption**: Local private keys (`cosign.key`) generated via `cosign generate-key-pair` must be encrypted at rest using scrypt key derivation and AES-256-GCM. Unencrypted private keys are prohibited.
2. **Passphrase Protection**: Passphrase must be provided via the `COSIGN_PASSWORD` environment variable or retrieved from NERO `SecretManager`. Raw passphrases must never be committed to Git or printed in pipeline logs.
3. **Filesystem Permissions**: Key files must enforce restricted access:
   - POSIX: `chmod 0600 cosign.key`
   - Windows: NTFS ACL restricted to the current runner service account (deny all other users).
4. **Key Backup and Recovery Runbook**: Author `docs/runbooks/COSIGN_KEY_MANAGEMENT_RUNBOOK.md` detailing secure offline backup of the encrypted private key and recovery procedures.
5. **Rotation Policy**: Define a 90-day key rotation cycle. Release manifests must record the `publicKeyId` used during signing to allow historic releases to verify against prior public keys.
6. **Compromise and Revocation Procedure**: If the private key is compromised, operators must revoke the key, mark affected releases as `REVOKED` in the catalog, append a `KEY_REVOCATION` record to `audit_log.jsonl`, and re-sign active release manifests with the new key.
7. **Offline Public-Key Verification**: Signatures must verify offline without internet egress:
   ```bash
   cosign verify --key platform_core/security/keys/cosign.pub localhost:5100/<image>@sha256:<digest>
   ```
8. **Audit Logging**: Every signing and verification event must emit a structured audit record containing signer identity, public key fingerprint, artifact digest, and timestamp.

---

## 7. Governance and Two-Person Approval Boundary

### 7.1 Existing Implementation Analysis
- **Current Pipeline**: [`ci-cd/jenkins/pipelines/universal/Jenkinsfile`](file:///d:/project/billing-system-master/billing-system-master/ci-cd/jenkins/pipelines/universal/Jenkinsfile#L443-L486) requests string inputs for `QA_APPROVER_NAME` and `OPS_APPROVER_NAME`.
- **Classification**: **`LOCAL_APPROVAL_SIMULATION`**.
- **Capabilities & Boundaries**:
  - [VERIFIED] Validates string inequality (`qa_approver != ops_approver`).
  - [VERIFIED] Fails closed if approver names or change ticket are missing or empty.
  - [VERIFIED] Validates change ticket format via regex (`changeTicket.startsWith('CHG-')`).
  - [VERIFIED] Appends approval records to the cryptographic audit ledger.
  - [NOT VERIFIED / LIMITATION] Does **not** bind identity to Jenkins HTTP session credentials (`UserIdCause`) or external IdP tokens. A single user can input two distinct strings to satisfy the gate.

---

### 7.2 Roadmap for Future Enterprise Authentication
To achieve enterprise compliance in cloud phases (A7/A9):
- **Phase A5**: Bind approver identity directly to Jenkins authenticated user ID (`env.BUILD_USER_ID` / `submitter`).
- **Phase A7**: Integrate SAML 2.0 / OIDC with corporate IdP (Okta, Azure AD) enforcing multi-factor authentication (MFA).
- **Phase A9**: Connect to ServiceNow / Jira Service Desk REST APIs to verify active, approved change tickets in real time.

---

## 8. Rollback Qualification Protocol

The "<30 second rollback" metric is classified as an **architectural design objective**, not a production SLA. 

### 8.1 Approach A: Initial Qualification Protocol (Local Lab Scope, $N = 5$)
- **Trial Count**: Exactly 5 consecutive independent trials per reference application.
- **Reporting Standards**:
  - Record and report all 5 raw durations ($T_1, T_2, T_3, T_4, T_5$).
  - Report **Median** ($T_{(3)}$) and **Maximum** ($\max(T)$).
  - **Zero P95 or P99 claims permitted** (mathematically invalid for $N=5$).
- **Cache Separation**: Execute 5 trials under **Warm Cache** (image present locally) and 5 trials under **Cold Cache** (image pulled from `localhost:5100`).
- **Timing Invariants**:
  - Measurement must use high-resolution monotonic clock (`time.monotonic()`).
  - Wall-clock timestamps recorded separately for audit ledger correlation.
  - $T_0$: Monotonic epoch when rollback command is initiated.
  - $T_1$: Monotonic epoch when all 7 synthetic health probes return HTTP 200.
  - Elapsed: $\Delta = T_1 - T_0$.
- **Pass/Fail Threshold**: $\text{Median} \le 30.0\text{ seconds}$ and $\text{Maximum} \le 45.0\text{ seconds}$ under Warm Cache.

---

### 8.2 Approach B: Statistical Performance Qualification (Future Scale Scope, $N \ge 30$)
- **Applicability**: Multi-node production or cloud ECS environments.
- **Sample Size**: Minimum $N = 30$ trials (or $N = 100$ for regulatory compliance).
- **Reporting Standards**: Report Mean, Median, Standard Deviation, P95, and P99 with 95% confidence intervals.
- **Prerequisites**: Must define representative concurrent user workloads, database background load, and network jitter distributions. Any future production percentile requirement must define a suitable sample size, workload distribution, measurement window, and statistical confidence.

---

## 9. Resource and Concurrency Constraints

### 9.1 Provisional Concurrency Bounding
- **Provisional Limit**: **`max_workers = 2`** in `BuildOrchestrator`.
- **Classification**: **`RECOMMENDATION`**.
- **Technical Context**: `max_workers = 2` is proposed as a **provisional conservative local execution limit**. It is **not** independently established as a guaranteed safe concurrency level, and no claim of a verified 6 GB peak-memory ceiling or guaranteed safe concurrency is made.
- **Qualitative Risk Factors**:
  - Maven compilation of Java 17 forks a JVM that can consume substantial memory.
  - Node.js frontend packaging via Vite/Rollup is memory-intensive during asset optimization.
  - Trivy and Semgrep AST scanning parsing polyglot source trees add memory overhead.
  - Core supporting containers (Jenkins, Postgres, Floci) operate concurrently.
  - On a 4-CPU, 8-GB RAM workstation, running 4 heavy parallel workers risks memory pressure or Docker container termination. Pinned provisionally at `max_workers = 2`, the operational load is substantially reduced.

---

### 9.2 Measurements Required to Qualify Safe Concurrency
Before increasing `max_workers` beyond 2 or claiming verified safe concurrency, the following empirical measurements must be conducted:
1. **Peak Memory Profile**: Continuous sampling of `working_set_bytes` during concurrent multi-component builds via Windows Performance Monitor (`perfmon`) or Docker stats.
2. **CPU Saturation**: Measurement of processor queue length (`System\Processor Queue Length`).
3. **Disk Throughput & Space**: Measurement of disk read/write throughput and space during layer extraction.
4. **Scanner Memory & Concurrency**: Profiling memory utilization of Semgrep, Trivy, and Gitleaks during concurrent scans.
5. **Workload Overhead**: Auditing Jenkins controller and application container memory footprints under load.
6. **System Stability Evidence**: Auditing system event logs for Docker OOM events or Windows memory paging spikes.

---

## 10. Cloud Execution Boundary

All cloud usage and expenditure evidence is strictly classified across four independent dimensions:

```text
===================================================================================================
                             CLOUD USAGE EVIDENCE CLASSIFICATION
===================================================================================================
```

| Dimension | Verification Status | Empirical Finding |
|---|:---:|---|
| **No AWS API Calls Observed** | **`VERIFIED`** | All SDK clients in the audited workflows target `http://localhost:4566` (Floci) or internal mocks. Zero network traffic to `amazonaws.com` was observed. |
| **No AWS Resources Provisioned** | **`VERIFIED`** | Inspecting `infrastructure/terraform/environments/local/terraform.tfstate` confirms that all 15 managed resources reside in local Floci state. Zero cloud infrastructure was provisioned. |
| **No Genuine AWS Credentials** | **`VERIFIED`** | Inspecting configurations confirms that only static mock strings (`floci`) are present. Zero real AWS secret access keys exist in the repository. |
| **AWS Billing Verification** | **`NOT VERIFIED`** | **Cannot be claimed**. No real AWS account or billing telemetry was accessed or inspected. Claiming "independently verified billing of $0.00" is removed. |

### Authoritative Local Execution Statement:
> *"All qualified local pipeline, testing and infrastructure workflows must target the local Floci and Docker environment using mock credentials. Real AWS provisioning and real AWS credential use are prohibited."*

*(Note: Zero public AWS network egress is claimed only where network telemetry actually demonstrates it).*

---

## 11. Phase A4 24-Task and Engineering-Hour Baseline

The official Phase A4 Work Breakdown Structure comprises **24 discrete engineering tasks across 6 milestones**:

```text
===================================================================================================
                       PHASE A4 AUTHORITATIVE WORK BREAKDOWN STRUCTURE
===================================================================================================
  Milestone ID & Title                           Tasks    Nominal EH   PERT Expected   Complexity
---------------------------------------------------------------------------------------------------
  M1: Candidate Ingestion & Manifest v2           4 tasks     30.0 EH         30.67 EH     Moderate
  M2: Registry Adapters & Distribution            4 tasks     32.0 EH         32.67 EH     Moderate
  M3: Software Supply Chain Security (Syft/Cosign)4 tasks     34.0 EH         34.67 EH     High
  M4: Release Qualification Engine & Policy Gates 4 tasks     32.0 EH         32.33 EH     High
  M5: Promotion Engine & Two-Person Gate          4 tasks     32.0 EH         32.67 EH     Moderate
  M6: Rollback, Retention, Revocation & E2E Suite 4 tasks     28.0 EH         28.33 EH     Moderate
---------------------------------------------------------------------------------------------------
  TOTAL PROGRAMME 1 PHASE A4 IMPLEMENTATION      24 tasks    188.0 EH        191.33 EH
===================================================================================================
```

- **Nominal Implementation Budget**: **188.0 Engineering Hours** (Sum of all 24 individual task Most-Likely estimates).
- **Statistical PERT Expected Effort**: **191.33 Engineering Hours** ($O=162.0, M=188.0, P=234.0$).
- **Estimated Calendar Duration**: Approximately **6 calendar weeks** (at 32 effective EH/week for 1 Senior Platform Engineer).
- **Corrective Action Scope**: Corrective Action `CORR-ACT-AUDIT-001` (audit ledger test isolation) is tracked separately as `NOT ESTIMATED` and does not alter this 188.0 EH baseline.

---

## 12. Risk Register

| Risk ID | Description | Severity | Likelihood | Impact | Mitigation Strategy | Blocks A4 Approval? |
|---|---|:---:|:---:|:---:|---|:---:|
| **RSK-001** | Unpinned Builder Image Tags in Go Service | High | High | High | Pin `golang:1.27.3-alpine3.24` and distroless to verified SHA-256 digests in `Dockerfile` as part of A4 Milestone 2. | **No** (Remediated in A4) |
| **RSK-002** | Test-Driven Audit Ledger Pollution | Medium | High | Low | Track `CORR-ACT-AUDIT-001` separately to implement `NERO_AUDIT_LOG_PATH` isolation in `conftest.py`. | **No** (Platform improvement) |
| **RSK-003** | Bitbucket SCM Gateway HTTP Unverified | Low | Medium | Low | Add Bitbucket live HTTP webhook test to `test_webhook_gateway.py` during A4 Candidate Ingestion. | **No** (Level 1 verified) |
| **RSK-004** | Local Cosign Key Custody Risk | High | Low | Critical | Protect `cosign.key` with AES-256-GCM; manage passphrase via `SecretManager`; deliver runbooks in M3. | **No** (Local boundary accepted) |
| **RSK-005** | Memory Pressure During Parallel Builds | Medium | Medium | Medium | Pin `max_workers = 2` as a provisional conservative limit in `BuildOrchestrator`. | **No** (Constraint codified) |
| **RSK-006** | Rollback Latency Exceeds 30s Target | Low | Medium | Low | Classify 30s as a design objective; evaluate using Section 8 Approach A ($N=5$) benchmark protocol. | **No** (Benchmarking defined) |

---

## 13. Three Independent Owner Approval Sections

The platform owner is presented with three independent, un-prefilled approval gates:

### Decision Gate 1: Phase A3 Formal Closure
- **Proposed Determination**: **`A3_CLOSURE_VERIFIED_WITH_EXCEPTIONS`**
- **Accepted Scope**:
  - Full local qualification of 24 Phase A3 tasks (139/139 tests in `tests/`, 153/153 repository-wide).
  - Accepted Exception 1: SCM Level 3 SaaS webhook delivery omitted (offline local lab).
  - Accepted Exception 2: Bitbucket qualified at Level 1 (fixtures); live HTTP routing deferred to A4.
  - Accepted Exception 3: Test-driven ledger pollution acknowledged; tracked as `CORR-ACT-AUDIT-001`.
- **Platform Owner Sign-Off**:
  - [ ] **I approve the formal closure of Phase A3 under `A3_CLOSURE_VERIFIED_WITH_EXCEPTIONS`.**
  - Approver Name: __________________________________________________
  - Signature / Token: _____________________________________________
  - Date: ___________________________________________________________

---

### Decision Gate 2: Phase A4 Architecture Approval
- **Proposed Determination**: **`A4_READY_WITH_CONDITIONS`**
- **Accepted Conditions**:
  - Condition 1: Go builder hermetic pinning using verified SHA-256 digests.
  - Condition 2: Cosign key lifecycle runbooks delivered in Milestone 3.
  - Condition 3: Two-person approval classified as `LOCAL_APPROVAL_SIMULATION`.
  - Condition 4: Rollback "<30s" classified as design objective governed by Section 8 Approach A.
  - Condition 5: Parallel build concurrency provisionally bounded to `max_workers = 2`.
  - Condition 6: Local execution boundary targeting Floci/Docker with zero real cloud spend.
- **Platform Owner Sign-Off**:
  - [ ] **I approve the Phase A4 Architecture Package under `A4_READY_WITH_CONDITIONS`.**
  - Approver Name: __________________________________________________
  - Signature / Token: _____________________________________________
  - Date: ___________________________________________________________

---

### Decision Gate 3: Phase A4 Implementation Authorization
- **Current Status**: **`PENDING OWNER AUTHORIZATION (STRICTLY HALTED)`**
- **Scope Authorized**:
  - Execution of 24 engineering tasks across 6 milestones.
  - Implementation effort: **188.0 Engineering Hours** nominal baseline (191.33 EH PERT expected; ~6 calendar weeks).
  - Infrastructure boundary: Local Floci/Docker execution; no AWS usage observed; Terraform Serial 23 baseline preservation.
  - Separate tracking of `CORR-ACT-AUDIT-001` (audit ledger test isolation).
- **Platform Owner Sign-Off**:
  - [ ] **I explicitly authorize commencing implementation of Phase A4 with 188.0 Engineering Hours under the specified local constraints.**
  - Approver Name: __________________________________________________
  - Signature / Token: _____________________________________________
  - Date: ___________________________________________________________

---

## 14. Explicit Implementation Authorization Boundary

In strict compliance with Programme 1 governance standards:
- **Zero Phase A4 implementation code has been authored or executed.**
- No Dockerfiles, application sources, Jenkins pipelines, or Terraform state files have been altered.
- **Phase A4 engineering implementation will begin ONLY after the platform owner explicitly executes Decision Gate 3 above.**

---

## 15. Supporting Document References

All findings in this package are anchored on the following authoritative architecture documents:
1. [NERO_A3_CLOSURE_VERIFICATION_REPORT.md](file:///d:/project/billing-system-master/billing-system-master/nero_devops_standard/docs/architecture/NERO_A3_CLOSURE_VERIFICATION_REPORT.md) — Phase A3 baseline task audit.
2. [NERO_A4_IMMUTABLE_RELEASE_REQUIREMENTS_ARCHITECTURE_AND_IMPLEMENTATION_PLAN.md](file:///d:/project/billing-system-master/billing-system-master/nero_devops_standard/docs/architecture/NERO_A4_IMMUTABLE_RELEASE_REQUIREMENTS_ARCHITECTURE_AND_IMPLEMENTATION_PLAN.md) — 24-task WBS and Release Manifest v2 schema.
3. [NERO_A4_ARTIFACT_REPOSITORY_COMPATIBILITY_MATRIX.md](file:///d:/project/billing-system-master/billing-system-master/nero_devops_standard/docs/architecture/NERO_A4_ARTIFACT_REPOSITORY_COMPATIBILITY_MATRIX.md) — Decoupled OCI + S3 registry architecture.
4. [NERO_A4_RELEASE_LIFECYCLE_AND_GOVERNANCE_MODEL.md](file:///d:/project/billing-system-master/billing-system-master/nero_devops_standard/docs/architecture/NERO_A4_RELEASE_LIFECYCLE_AND_GOVERNANCE_MODEL.md) — Zero-Rebuild promotion and rollback governance.
5. [NERO_A3_A4_AUDIT_RECONCILIATION_AND_OWNER_DECISION_PACK.md](file:///d:/project/billing-system-master/billing-system-master/nero_devops_standard/docs/architecture/NERO_A3_A4_AUDIT_RECONCILIATION_AND_OWNER_DECISION_PACK.md) — Preliminary audit reconciliation.
6. [NERO_FINAL_OWNER_SIGNOFF_EVIDENCE_REPORT.md](file:///d:/project/billing-system-master/billing-system-master/nero_devops_standard/docs/architecture/NERO_FINAL_OWNER_SIGNOFF_EVIDENCE_REPORT.md) — Empirical evidence audit report.

---
*End of Document NERO-A3-A4-FINAL-DECISION-PKG-002. All implementation activities remain halted pending owner sign-off.*
