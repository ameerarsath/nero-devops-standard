# NERO Enterprise DevOps Automation Platform
# Phase A4 Implementation Readiness & Kickoff Preparation Plan
## Immutable Release Engineering & Artifact Repository Integration

**Document ID:** NERO-A4-KICKOFF-PLAN-001  
**Date:** November 9, 2026  
**Author:** Principal DevOps Architect, Senior Platform Engineer & Technical Implementation Lead  
**Classification:** Authoritative Technical Plan & Owner Briefing  
**Target Repository:** `D:\project\billing-system-master\billing-system-master`  
**Target Git Branch:** `devops/jenkins-floci-local-lab`  
**Governing Baseline:** `NERO_FINAL_A3_A4_OWNER_DECISION_PACKAGE_v2.md` & `NERO_OWNER_DECISION_001.md`  

---

## 1. Executive Overview

### 1.1 Governance Posture & Operating State
The Platform Owner has formally issued decisions on the first two gates of Programme 1:
- **Gate 1 — Phase A3 Continuous Integration Automation Closure**: **APPROVED** (`A3_CLOSURE_VERIFIED_WITH_EXCEPTIONS`).
- **Gate 2 — Phase A4 Immutable Release Architecture**: **APPROVED WITH CONDITIONS** (`A4_READY_WITH_CONDITIONS`).
- **Gate 3 — Phase A4 Implementation Authorization**: **PENDING OWNER AUTHORIZATION** (**STRICTLY HALTED**).

```text
+===================================================================================================+
|                                    CURRENT GOVERNANCE POSTURE                                     |
+===================================================================================================+
|  Gate 1: Phase A3 Closure          --> APPROVED (A3_CLOSURE_VERIFIED_WITH_EXCEPTIONS)             |
|  Gate 2: Phase A4 Architecture     --> APPROVED WITH CONDITIONS (A4_READY_WITH_CONDITIONS)        |
|  Gate 3: Phase A4 Implementation   --> PENDING OWNER AUTHORIZATION (IMPLEMENTATION HALTED)        |
+===================================================================================================+
```

### 1.2 Purpose of This Document
This document is a comprehensive kickoff and readiness briefing prepared specifically for the Platform Owner. Its objectives are:
1. To explain the architecture, mechanics, and business value of Phase A4 in clear, accessible language.
2. To codify the 6-milestone, 24-task execution roadmap (188.0 EH nominal, 191.33 EH PERT expected, ~6 calendar weeks) without deviation from the approved baseline.
3. To resolve all binding architecture conditions established during Gate 2 approval.
4. To define the exact blueprint for the very first implementation session (`A4-CAN-001`) so the owner can inspect what will happen before any code is written.
5. To provide a rigorous Stop/Go Authorization Checklist and plain-language summary for Gate 3 consideration.

> [!IMPORTANT]
> **Strict Operational Boundary**: This document is produced under a strict READ-ONLY protocol. No implementation code has been written, no existing pipeline or Dockerfile has been altered, no containers have been restarted, no Terraform state has been touched, and no Git commits or pushes have been performed. Phase A4 implementation remains paused pending explicit owner authorization.

---

## 2. Beginner-Friendly Explanation of Phase A4 Concepts

To ensure the Platform Owner and platform stakeholders have absolute clarity on what Phase A4 builds, this section explains the 12 core concepts using real examples from the existing reference applications (the `hotel-billing` system with its Spring Boot backend and React/Vite frontend, plus the Go, Node.js, and Python microservices).

```text
+---------------------------------------------------------------------------------------------------+
|                                  THE 12 PILLARS OF PHASE A4                                       |
+---------------------------------------------------------------------------------------------------+
|   1. Immutable Releases               2. Container Image Digests          3. Software Bill of Mat. |
|   4. Software Provenance              5. Cosign Digital Signatures        6. Universal Manifest v2 |
|   7. OCI Registry Architecture        8. Floci S3 Storage                 9. 12-Step Qualification |
|  10. Zero-Rebuild Promotion          11. Two-Person Production Gate      12. Deterministic Rollback|
+---------------------------------------------------------------------------------------------------+
```

---

### Concept 1: What Immutable Releases Mean
- **The Concept**: In traditional, flawed software setups, code is recompiled or rebuilt every time it moves to a new environment (e.g., built on a developer's laptop, re-built on a test server, re-built for staging, and rebuilt again for production). This introduces "environmental drift"—different compiler versions, updated external dependencies, or timing discrepancies can mean the code running in production is slightly different from the code that was tested in QA.
- **The Solution**: An **immutable release** means the software binaries are built and packaged **exactly once** during the CI build. Once packaged, that binary is sealed like a tamper-evident medicine bottle. It is never recompiled, re-packaged, or altered. The identical, byte-for-byte binary tested in QA is promoted into production.
- **Example in NERO**: For `hotel-billing`, the Java Spring Boot backend `.jar` and its container image are constructed once. When moving from `develop` to `qa` to `prod`, the container image is never rebuilt. Only runtime configuration (database connection strings, secrets) is injected externally.

---

### Concept 2: Why Container Image Digests Are Important
- **The Concept**: Container images are commonly referred to by human-readable "tags", such as `hotel-billing-backend:latest` or `:1.0.0`. However, tags are **mutable pointers** (like sticky labels). Anyone with registry access can overwrite a tag with a completely different image tomorrow. If an automated system pulls `:latest`, it cannot guarantee what code it is actually running.
- **The Solution**: A **container image digest** is a 64-character SHA-256 cryptographic hash calculated over the exact compressed contents of the image (e.g., `sha256:4f8a91c8...`). If even a single byte, configuration file, or timestamp inside the container changes, the hash changes completely. Referencing an image by its digest (`image@sha256:...`) mathematically guarantees that you run the exact same code every time, on any machine, forever.
- **Example in NERO**: In `sample-go-service/Dockerfile`, rather than relying on `golang:alpine` (which can change at any time), we pin the exact builder digest `golang:1.27.3-alpine3.24@sha256:0fd028db...` and runtime digest `gcr.io/distroless/static-debian12:nonroot@sha256:52dcfbab...`.

---

### Concept 3: What a Software Bill of Materials (SBOM) Is
- **The Concept**: When an application is compiled, it incorporates dozens or hundreds of open-source third-party libraries (e.g., Spring Boot, Hibernate, Jackson, React, Vite, Axios). In the past, companies had no centralized inventory of what components were embedded inside their shipped binaries.
- **The Solution**: An **SBOM** (Software Bill of Materials) is the software equivalent of an ingredients label and nutrition facts sheet on a food package. It lists every package, library, transitive dependency, version, and software license inside the binary. NERO uses the industry-standard **CycloneDX 1.5 JSON** format generated automatically by `Syft`.
- **Example in NERO**: When a new zero-day vulnerability (such as a Log4j or OpenSSL vulnerability) is published in the national vulnerability database, operators do not need to read source code or scan live servers. They simply run an automated query against the stored CycloneDX SBOMs to identify every running service affected within seconds.

---

### Concept 4: What Software Provenance Means
- **The Concept**: How do you prove that a binary running on a server was legitimately built by your automated Jenkins pipeline from an approved Git commit, rather than built on a rogue developer's compromised laptop or injected by a supply-chain attacker?
- **The Solution**: **Software Provenance** is a verifiable digital certificate of origin. Using the **in-toto v1.0** attestation format (aligning with SLSA Level 3 standards), the build system records:
  1. The exact source Git repository and commit SHA (`a9482b8...`).
  2. The build pipeline and executor identity (`jenkins-ci@trusted-agent`).
  3. The build parameters, environment variables, and timestamps.
  4. The cryptographic hashes of all generated artifacts.
- **Example in NERO**: Before `hotel-billing` can be deployed, the platform verifies the in-toto attestation to ensure the binary was built exclusively inside our isolated Jenkins container directly from the authorized branch.

---

### Concept 5: What Cosign Does
- **The Concept**: Anyone can copy an image into a container registry. Without digital signatures, there is no way for a deployment engine to verify whether an image is authentic and trustworthy.
- **The Solution**: **Cosign** (part of the Linux Foundation's Sigstore project) provides public/private cryptographic signing for container images. During the build, Jenkins uses a protected private key (`cosign.key`) to calculate a digital signature over the image's SHA-256 digest. This signature is stored in the registry alongside the image. Before deploying, the runtime verifies the signature using the open public key (`cosign.pub`).
- **Example in NERO**: If an unauthorized party modifies a container image in our local registry (`localhost:5100`), the image digest changes, and the Cosign signature immediately becomes invalid. The deployment engine detects the signature mismatch and blocks deployment instantly.

---

### Concept 6: Why Release Manifests Are Needed
- **The Concept**: Enterprise systems are rarely composed of a single file. The `hotel-billing` system consists of:
  - A backend Java container image.
  - A frontend React static web bundle.
  - Database schema migration files.
  - Runtime environment configurations.
  - Associated SBOMs, test reports, and signatures.
- **The Solution**: A **Release Manifest** (`release_manifest_v2.json`) is the single authoritative contract that ties all these components together into a single, cohesive release package (e.g., `rel-hotel-qual-01`). It records the component names, storage locations, exact cryptographic digests, test pass rates, diff coverage scores, and approvals.
- **Example in NERO**: The release manifest acts like a signed bill of lading for a shipping container. It guarantees that the backend version `1.0.0` is deployed with the exact matching frontend version `1.0.0` that was tested with it.

---

### Concept 7: How OCI Registry Storage Works
- **The Concept**: Container images and modern cloud artifacts must be stored in standardized, high-performance repositories accessible over HTTP APIs.
- **The Solution**: The **Open Container Initiative (OCI)** defines global standards for container images and registries. An OCI registry stores content as content-addressable blobs indexed by their SHA-256 digests. If two different services share the same base operating system layer, the registry stores it only once, saving disk space and network bandwidth.
- **Example in NERO**: NERO runs an internal, high-speed OCI Distribution v2 compliant registry at `localhost:5100`. In Phase A4, this registry stores not only container images but also Cosign signatures (`image:sha256-<digest>.sig`) and in-toto attestations as native OCI artifacts.

---

### Concept 8: Why Floci S3 Storage Is Used
- **The Concept**: Not all deployable assets are container images. For instance, the React/Vite frontend for `hotel-billing` is compiled into static web files (HTML, JavaScript, CSS). In production AWS environments, static frontends are deployed to Amazon S3 buckets behind CloudFront content delivery networks.
- **The Solution**: **Floci** (`localhost:4566`) is our local cloud emulator that replicates AWS S3 APIs with 100% fidelity on developer workstations. By storing frontend tarballs and release manifests in Floci S3, we achieve full enterprise cloud compatibility and zero operational disruption while maintaining **$0.00 cloud spend**.
- **Example in NERO**: During a release, the frontend bundle is uploaded to `s3://nero-releases-local/hotel-billing/rel-20261108193000/frontend.tar.gz`. The S3 adapter calculates and verifies the SHA-256 checksum during upload and retrieval.

---

### Concept 9: What Release Qualification Means
- **The Concept**: Continuous Integration (Phase A3) validates that individual code commits compile and pass unit tests. However, passing unit tests does not mean a package is ready for enterprise release. A release must meet rigorous platform policies before it is permitted near production.
- **The Solution**: **Release Qualification** is an automated 12-step gate evaluated by the `ReleaseQualificationEngine`. It validates:
  1. Candidate contract schema integrity.
  2. Service catalog registration and branch authorization.
  3. Git commit non-repudiation (exists on remote origin).
  4. Component presence in OCI registry / S3.
  5. Cryptographic digest parity.
  6. CycloneDX SBOM completeness.
  7. In-toto build provenance validity.
  8. Cosign digital signature verification.
  9. Security gate compliance (0 unexempted HIGH/CRITICAL CVEs, 0 secrets, 0 SAST blockers).
  10. Changed-code diff coverage $\ge 80.0\%$.
  11. Target environment resource compatibility (ports, CPU, memory).
  12. Rollback readiness (prior release identified, non-breaking schema).
- **Outcome**: A candidate release transitions to `QUALIFIED` only if all 12 checks pass. If any check fails, it is marked `REJECTED`.

---

### Concept 10: How Zero-Rebuild Promotion Works
- **The Concept**: In legacy pipelines, moving an application from QA to Staging to Production often triggered a new build command with different flags. This was dangerous because code could behave differently or pick up newer library versions.
- **The Solution**: **Zero-Rebuild Promotion** means that moving between environments never recompiles code. The deployment coordinator takes the exact immutable manifest minted during qualification and applies it to the target environment. The container runtime pulls the exact pinned SHA-256 digest. Environment-specific settings (database hosts, API keys) are supplied at runtime via environment variables or secret managers.
- **Example in NERO**: Promoting `hotel-billing` from `develop` to `qa` takes under 10 seconds: the pipeline verifies the digest parity, updates the container definition to point to the qualified digest, and verifies health endpoints. Not a single line of Java or TypeScript is recompiled.

---

### Concept 11: How Two-Person Production Approval Works
- **The Concept**: Enterprise governance frameworks (SOX, SOC 2, ISO 27001) mandate the "Four-Eyes Principle": no single person can write code, approve their own release, and push it to production. There must be independent verification.
- **The Solution**: Before any release can be promoted into the `prod` environment, the deployment pipeline halts at an approval gate. It requires two distinct human roles:
  1. A Requester (the engineer requesting deployment).
  2. An Independent Approver (QA Lead or Operations Lead).
  3. An active change management ticket reference (e.g., `CHG-2026-1109`).
- **Local Implementation Boundary**: In our local lab, this is implemented as `LOCAL_APPROVAL_SIMULATION`. The pipeline verifies that the two approver strings are non-empty and non-identical, and checks the ticket format. If either requirement fails, the pipeline **fails closed** (aborts immediately).

---

### Concept 12: How Rollback Restores a Previous Release
- **The Concept**: If a newly promoted release experiences unforeseen issues in production (e.g., unexpected latency spikes or edge-case runtime exceptions), operators must restore the system to a healthy state as quickly as possible.
- **The Solution**: Because every release is immutably archived with its exact manifest, container digests, and frontend assets, rollback does not require re-running builds or guessing configurations. The `RollbackEngine` executes an automated 10-step sequence:
  1. Validates rollback authorization.
  2. Identifies the prior stable release manifest (marked `SUPERSEDED`).
  3. Checks database schema compatibility (ensuring backward compatibility).
  4. Gracefully stops the failing containers.
  5. Points container definitions back to the previous pinned image digest.
  6. Restores the prior frontend static assets from S3.
  7. Restarts containers with previous environment parameters.
  8. Executes synthetic health checks across 7 endpoints.
  9. Appends a `RELEASE_ROLLED_BACK` event to the cryptographic audit ledger.
  10. Emits operational notifications.
- **Engineering Target**: Restores operational service in **less than 30 seconds** without recompilation.

---

## 3. Existing Architecture, Asset Reuse & A3 Integration

### 3.1 Local Laboratory Infrastructure
The NERO local platform currently operates completely offline with zero internet egress requirements and zero cloud charges:

```text
+---------------------------------------------------------------------------------------------------+
|                                 NERO LOCAL LAB INFRASTRUCTURE                                     |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|  [Jenkins Controller]           [Local OCI Registry]              [Floci Cloud Emulator]          |
|  Port: localhost:8080           Port: localhost:5100              Port: localhost:4566            |
|  Status: Healthy                Status: Healthy                   Status: Healthy                 |
|  Role: CI/CD Orchestration      Role: OCI Images & Signatures     Role: S3 Buckets & Secrets      |
|                                                                                                   |
|  [PostgreSQL Primary]           [PostgreSQL Secondary]            [Audit Ledger]                  |
|  Port: localhost:5432           Port: localhost:5434              Path: platform_core/audit/      |
|  Status: Healthy                Status: Healthy                   Status: 84 Records (Verified)   |
|                                                                                                   |
|  [Terraform Baseline]           [Reference Applications]          [Git Repository]                |
|  State: Serial 23 (15 Res.)     4 Apps: Hotel, Go, Node, Python   Branch: devops/jenkins-floci... |
+---------------------------------------------------------------------------------------------------+
```

---

### 3.2 How Phase A4 Integrates with Phase A3
Phase A3 (Continuous Integration Automation) and Phase A4 (Release Engineering) are cleanly decoupled:
1. **A3 Responsibility**: Triggers on Git webhooks (pushes, pull requests). Executes preflight checks, parallel multi-component builds, unit tests, code quality analysis (80% diff coverage enforcement), and security scanning (Gitleaks, Semgrep, Trivy). Outputs intermediate `ci_evidence.json` and compiled candidate artifacts.
2. **A4 Ingestion**: A4 begins where A3 ends. The A4 `CandidateIngestionEngine` consumes `ci_evidence.json` and validates the `CandidateReleaseContract`.
3. **Pipeline Decoupling**: CI runs inside `ci-cd/jenkins/pipelines/universal/Jenkinsfile`. Release Engineering runs inside a dedicated, isolated pipeline: `ci-cd/jenkins/pipelines/release/Jenkinsfile.release`.

```text
+---------------------------------------------------------------------------------------------------+
|                                 CI/CD PIPELINE DECOUPLING ARCHITECTURE                            |
+---------------------------------------------------------------------------------------------------+
|  Jenkinsfile.ci (Phase A3 CI Pipeline)       |  Jenkinsfile.release (Phase A4 Release Pipeline)   |
|  Trigger: Git Webhook (Push / PR)            |  Trigger: Successful CI or Manual Release Action   |
|  - Secret Scanning (Gitleaks)                |  - Candidate Ingestion (CandidateReleaseContract)  |
|  - Parallel Component Builds                 |  - OCI Distribution & Floci S3 Upload              |
|  - Automated Testing & JUnit Aggregation     |  - CycloneDX SBOM & in-toto Provenance Attestation |
|  - Code Quality & 80% Diff Coverage          |  - Cosign ECDSA P-256 Digital Signing              |
|  - SAST & SCA Scanning (Semgrep, Trivy)      |  - 12-Step Release Qualification Checklist         |
|  - Intermediate CI Evidence Emission         |  - Universal Release Manifest v2 Minting           |
|                                              |  - Release Catalog Registration & Audit Logging    |
|                                              |  - Zero-Rebuild Environment Promotion & Rollback   |
+---------------------------------------------------------------------------------------------------+
```

---

### 3.3 Reusable Assets Inventory
To maximize engineering efficiency and prevent duplicate code, Phase A4 reuses and extends existing platform modules:

| Existing Platform Module | File Location | How Phase A4 Reuses It |
|---|---|---|
| **CI Evidence Aggregator** | `platform_core/engine/ci_evidence.py` | Supplies raw test, coverage, and security data for `CandidateReleaseContract`. |
| **Audit Logger Subsystem** | `platform_core/audit/audit_logger.py` | Appends SHA-256 chained records for qualification, signing, promotion, and rollback. |
| **Security Exceptions Engine** | `platform_core/policy/security_exceptions.py` | Evaluates active security waivers (`.nero-security-exceptions.yaml`) during Step 9. |
| **Secret Scanner Adapter** | `platform_core/security/secret_scanner.py` | Reuses Gitleaks integration for release preflight secret checks. |
| **Diff Coverage Gate** | `platform_core/engine/coverage_gate.py` | Verifies the 80.0% changed-code coverage requirement during qualification Step 10. |
| **Service Catalog** | `platform_core/engine/catalog.py` | Validates application metadata, port allocations, and authorized release branches. |
| **OCI Adapter (v1)** | `platform_core/adapters/registry/oci_adapter.py` | Extended into `BaseRegistryAdapter` implementation with client-side immutability. |
| **Release & Rollback Managers (v1)**| `platform_core/engine/release_manager.py` | Logic refactored and wrapped into typed `ReleaseManifestV2` and `RollbackEngine`. |
| **Base Adapter Interface** | `platform_core/adapters/base.py` | Provides foundational error handling and execution abstractions for new adapters. |

---

## 4. Complete 24-Task Execution Plan Across Six Milestones

The approved Phase A4 implementation baseline comprises **24 discrete engineering tasks** organized across **6 milestones**, totaling **188.0 Nominal Engineering Hours** (191.33 EH PERT expected).

```text
+===================================================================================================+
|                               PHASE A4 WORK BREAKDOWN OVERVIEW                                    |
+===================================================================================================+
| Milestone 1: Candidate Ingestion & Release Manifest Architecture                30.0 EH  (Tasks 1-4)  |
| Milestone 2: Registry Adapter Expansion & Multi-Artifact Distribution            32.0 EH  (Tasks 5-8)  |
| Milestone 3: Software Supply Chain Security — Syft & Cosign                      34.0 EH  (Tasks 9-12) |
| Milestone 4: Release Qualification Engine & Policy Gates                         32.0 EH  (Tasks 13-16)|
| Milestone 5: Promotion Engine & Two-Person Production Gate                       32.0 EH  (Tasks 17-20)|
| Milestone 6: Rollback Engineering, Retention, Revocation & E2E Suite             28.0 EH  (Tasks 21-24)|
+---------------------------------------------------------------------------------------------------+
| TOTAL PHASE A4 IMPLEMENTATION BASELINE                                          188.0 EH  (24 Tasks)|
+===================================================================================================+
```

---

### Milestone 1: Candidate Ingestion & Release Manifest Architecture (30.0 EH)
- **Objective**: Establish the formal Pydantic v2 data models, candidate ingestion engine, and manifest serialization subsystem required to ingest CI outputs and mint immutable release contracts.
- **Tasks**:
  1. `A4-CAN-001: Candidate Release Contract Model` (8.0 EH)  
     *File*: `platform_core/models/candidate_contract.py`  
     *Scope*: Implement typed Pydantic v2 models validating CI evidence, test pass rates, diff coverage, and SHA-256 digests.
  2. `A4-CAN-002: Candidate Ingestion & Preflight Validator` (8.0 EH)  
     *File*: `platform_core/engine/candidate_ingest.py`  
     *Scope*: Parse `ci_evidence.json`, verify origin Git commit SHA, and validate catalog authorization.
  3. `A4-MAN-001: Universal Release Manifest v2 Schema` (8.0 EH)  
     *File*: `platform_core/models/release_manifest_v2.py`  
     *Scope*: Formal model representing multi-component releases, OCI images, tarballs, SBOMs, signatures, and promotions.
  4. `A4-MAN-002: Manifest Serializer & Catalog Registrar` (6.0 EH)  
     *File*: `platform_core/engine/release_manifest.py`  
     *Scope*: Deterministic JSON serialization, payload SHA-256 calculation, and local catalog indexing.
- **Dependencies**: Existing `ci_evidence.py`, `catalog.py`, `release_manager.py`.
- **Expected Deliverables**: Pydantic v2 models, ingestion validator, manifest generator, and unit test suites.
- **Tests Required**: `tests/unit/test_candidate_contract.py`, `tests/unit/test_candidate_ingest.py`, `tests/unit/test_release_manifest_v2.py`.
- **Security Requirements**: Contract validation must fail closed on missing digests, test failures, or coverage $<80\%$.
- **Acceptance Criteria**: Ingests valid CI evidence cleanly; rejects malformed contracts; manifests achieve byte-level deterministic serialization.
- **Risks & Rollback**: Low risk. Isolated new Python files. Rollback entails deleting newly created module files.

---

### Milestone 2: Registry Adapter Expansion & Multi-Artifact Distribution (32.0 EH)
- **Objective**: Provide robust, content-addressable storage adapters for pushing container images to the local OCI registry and static frontend bundles to Floci S3.
- **Tasks**:
  5. `A4-REG-001: BaseRegistryAdapter Interface` (6.0 EH)  
     *File*: `platform_core/adapters/registry/base.py`  
     *Scope*: Define abstract base class for registry operations (`publish_image`, `retrieve_manifest`, `verify_digest`, `apply_retention`).
  6. `A4-REG-002: Expanded OCI Distribution Adapter` (10.0 EH)  
     *File*: `platform_core/adapters/registry/oci_adapter.py`  
     *Scope*: Client-side tag immutability, canonical 64-character digest verification, and OCI artifact upload against `localhost:5100`. Pin Go builder and Distroless runtime digests.
  7. `A4-REG-003: S3 Static Artifact Release Adapter` (8.0 EH)  
     *File*: `platform_core/adapters/registry/s3_release_adapter.py`  
     *Scope*: Upload static frontend tarballs to Floci S3 with streaming SHA-256 calculation and zero-rebuild retrieval.
  8. `A4-REG-004: Multi-Component Distribution Dispatcher` (8.0 EH)  
     *File*: `platform_core/engine/distribution_dispatcher.py`  
     *Scope*: Concurrent dispatch of backend containers to OCI registry and frontend assets to S3 with atomic fail-closed rollback.
- **Dependencies**: Milestone 1, running OCI registry (`localhost:5100`), running Floci S3 (`localhost:4566`).
- **Expected Deliverables**: Registry adapter hierarchy, S3 release adapter, distribution dispatcher.
- **Tests Required**: `tests/unit/test_oci_adapter.py`, `tests/unit/test_s3_release_adapter.py`, `tests/unit/test_distribution_dispatcher.py`.
- **Security Requirements**: Must reject tag overwrite attempts; must verify remote SHA-256 digest matches local artifact hash before confirming upload.
- **Acceptance Criteria**: Pushes images and tarballs; fails closed if any component upload encounters an error.
- **Risks & Rollback**: Registry connection failure or S3 bucket missing. Mitigated by automated bucket provisioning and offline fallback mocks in unit tests.

---

### Milestone 3: Software Supply Chain Security — Syft & Cosign (34.0 EH)
- **Objective**: Implement end-to-end software supply-chain security aligning with SLSA Level 3, including CycloneDX SBOM generation, in-toto build provenance, and local Cosign ECDSA P-256 digital signing.
- **Tasks**:
  9. `A4-SEC-001: Syft SBOM Generation Adapter` (10.0 EH)  
     *File*: `platform_core/adapters/security/syft_adapter.py`  
     *Scope*: Generate CycloneDX 1.5 JSON SBOMs for container images and project directories with package enumeration and license metadata.
  10. `A4-SEC-002: In-Toto Build Provenance Attestation` (8.0 EH)  
      *File*: `platform_core/adapters/security/provenance_adapter.py`  
      *Scope*: Generate SLSA-compliant in-toto v1.0 provenance linking Git commit, builder identity, environment parameters, and artifact hashes.
  11. `A4-SEC-003: Cosign Digital Signing Adapter` (10.0 EH)  
      *File*: `platform_core/adapters/security/cosign_adapter.py` & `docs/runbooks/COSIGN_KEY_MANAGEMENT_RUNBOOK.md`  
      *Scope*: Generate local ECDSA P-256 keypair, encrypt private key with AES-256-GCM, integrate passphrase handling with `SecretManager`, sign images, and upload signatures to registry.
  12. `A4-SEC-004: Supply Chain Evidence Aggregator` (6.0 EH)  
      *File*: `platform_core/engine/supply_chain_aggregator.py`  
      *Scope*: Aggregate image digests, SBOMs, provenance records, and Cosign signatures into the release manifest.
- **Dependencies**: Milestones 1 and 2, local Cosign and Syft tools / pure-Python cryptographic fallbacks.
- **Expected Deliverables**: Syft adapter, Provenance adapter, Cosign signing adapter, key management runbook.
- **Tests Required**: `tests/unit/test_syft_adapter.py`, `tests/unit/test_provenance_adapter.py`, `tests/unit/test_cosign_adapter.py`, `tests/unit/test_supply_chain_aggregator.py`.
- **Security Requirements**: Private keys must be encrypted at rest; passphrases must never be logged or committed; signatures must verify offline without internet egress.
- **Acceptance Criteria**: Generates valid CycloneDX 1.5 JSON; generates valid in-toto v1.0 attestations; Cosign signs and verifies images offline against `localhost:5100`.
- **Risks & Rollback**: Cosign CLI missing in environment. Mitigated by robust pure-Python ECDSA verification fallback.

---

### Milestone 4: Release Qualification Engine & Policy Gates (32.0 EH)
- **Objective**: Implement the automated 12-Step Release Qualification Checklist, the Release Finite State Machine (FSM), security policy enforcement, and audit ledger integration.
- **Tasks**:
  13. `A4-QLF-001: 12-Step Release Qualification Engine` (10.0 EH)  
      *File*: `platform_core/engine/release_qualification.py`  
      *Scope*: Implement all 12 checklist verification steps returning structured pass/fail reports and remediation guidance.
  14. `A4-QLF-002: Release Finite State Machine (FSM)` (8.0 EH)  
      *File*: `platform_core/engine/release_fsm.py`  
      *Scope*: Enforce legal state transitions (`CANDIDATE` $\rightarrow$ `QUALIFIED` $\rightarrow$ `PROMOTED` $\rightarrow$ `SUPERSEDED` / `REVOKED`) and block illegal promotion attempts.
  15. `A4-QLF-003: Release Security Policy Validator` (8.0 EH)  
      *File*: `platform_core/policy/release_policy.py`  
      *Scope*: Assert zero unexempted HIGH/CRITICAL CVEs, zero secrets, zero SAST blockers, and verify active security waivers.
  16. `A4-QLF-004: Release Audit Ledger Integrator` (6.0 EH)  
      *File*: `platform_core/audit/release_audit.py`  
      *Scope*: Append tamper-evident `RELEASE_QUALIFIED`, `RELEASE_REJECTED`, and `RELEASE_MINTED` records to `audit_log.jsonl` under cross-platform file locking.
- **Dependencies**: Milestones 1, 2, 3; existing `audit_logger.py` and `security_exceptions.py`.
- **Expected Deliverables**: Qualification engine, release FSM, security policy gate, audit logger extensions.
- **Tests Required**: `tests/unit/test_release_qualification.py`, `tests/unit/test_release_fsm.py`, `tests/unit/test_release_policy.py`, `tests/unit/test_release_audit.py`.
- **Security Requirements**: Any failure across the 12 steps must immediately halt qualification and transition the release to `REJECTED`. Audit records must preserve unbroken SHA-256 chains.
- **Acceptance Criteria**: Successfully qualifies compliant releases; catches and rejects non-compliant candidate artifacts; records all transitions in audit log.
- **Risks & Rollback**: Audit file lock contention. Mitigated by existing atomic retry file-locking mechanism in `audit_logger.py`.

---

### Milestone 5: Promotion Engine & Two-Person Production Gate (32.0 EH)
- **Objective**: Implement zero-rebuild environment promotion, the two-person production governance gate, and dedicated Jenkins release pipeline integration.
- **Tasks**:
  17. `A4-PRM-001: Zero-Rebuild Promotion Engine` (10.0 EH)  
      *File*: `platform_core/engine/promotion_engine.py`  
      *Scope*: Dispatch immutable releases across environments without recompilation; verify byte-for-byte digest parity in target environments.
  18. `A4-PRM-002: Two-Person Production Governance Gate` (10.0 EH)  
      *File*: `platform_core/policy/two_person_gate.py`  
      *Scope*: Enforce distinct Requester vs Approver identities and validate change ticket format (`CHG-*`); fail closed if criteria are not satisfied.
  19. `A4-PRM-003: Release Declarative Jenkinsfile` (8.0 EH)  
      *File*: `ci-cd/jenkins/pipelines/release/Jenkinsfile.release`  
      *Scope*: Multi-stage declarative release pipeline orchestrating candidate ingestion, qualification, signing, and promotion.
  20. `A4-PRM-004: Trusted Shared Library Release Steps` (4.0 EH)  
      *File*: `ci-cd/jenkins/shared-library/vars/neroRelease.groovy`  
      *Scope*: Reusable Groovy pipeline steps for qualification, digital signing, and zero-rebuild promotion.
- **Dependencies**: Milestones 1-4; running Jenkins controller (`localhost:8080`).
- **Expected Deliverables**: Promotion engine, governance gate, declarative release Jenkinsfile, Groovy shared library step.
- **Tests Required**: `tests/unit/test_promotion_engine.py`, `tests/unit/test_two_person_gate.py`, Jenkins pipeline syntax linting.
- **Security Requirements**: Production promotion must fail closed if approver names match requester, if change ticket is invalid, or if release status is not `QUALIFIED`.
- **Acceptance Criteria**: Successfully promotes releases to target environments; verifies digest parity; blocks unauthorized promotions.
- **Risks & Rollback**: Jenkins job misconfiguration. Mitigated by creating a separate `universal-release-pipeline` job without touching the active `universal-ci-pipeline`.

---

### Milestone 6: Rollback Engineering, Retention, Revocation & E2E Suite (28.0 EH)
- **Objective**: Implement automated 10-step rollback orchestrator, artifact retention sweeper, release revocation coordinator, and the comprehensive end-to-end integration test suite.
- **Tasks**:
  21. `A4-ROL-001: Deterministic Rollback Orchestrator` (8.0 EH)  
      *File*: `platform_core/engine/rollback_engine.py`  
      *Scope*: Implement 10-step rollback redeploying prior immutable release manifest; benchmark execution duration using Approach A ($N=5$).
  22. `A4-RET-001: Artifact Lifecycle & Retention Sweeper` (6.0 EH)  
      *File*: `platform_core/policy/retention_sweeper.py`  
      *Scope*: Enforce environment retention tiers; purge orphaned tags while protecting active deployments and rollback dependencies.
  23. `A4-REV-001: Release Revocation Coordinator` (6.0 EH)  
      *File*: `platform_core/policy/revocation_coordinator.py`  
      *Scope*: Mark compromised releases as `REVOKED`; block subsequent promotions; emit audit alerts.
  24. `A4-TST-001: End-to-End Release Qualification Suite` (8.0 EH)  
      *File*: `tests/integration/test_release_engineering.py`  
      *Scope*: Automated end-to-end test suite qualifying all 4 reference applications through release, promotion, and rollback.
- **Dependencies**: Milestones 1-5; all reference application configurations.
- **Expected Deliverables**: Rollback engine, retention sweeper, revocation coordinator, comprehensive E2E test suite.
- **Tests Required**: `tests/unit/test_rollback_engine.py`, `tests/unit/test_retention_sweeper.py`, `tests/unit/test_revocation_coordinator.py`, `tests/integration/test_release_engineering.py`.
- **Security Requirements**: Revoked releases must be permanently blocked from promotion; retention sweeper must never delete active or rollback images.
- **Acceptance Criteria**: Rollback completes reliably in $<30$ seconds (design target); retention policies preserve active images; 100% of integration tests pass.
- **Risks & Rollback**: Complex multi-container state transitions during rollback. Mitigated by strict synthetic health checks and fallback to manual container restart if rollback fails.

---

## 5. Engineering Effort Allocation & Resource Planning

### 5.1 Three-Point PERT Effort Estimation
Using the approved three-point estimation model ($E = \frac{O + 4M + P}{6}$):

| Milestone | Nominal ($M$) | Optimistic ($O$) | Pessimistic ($P$) | PERT Expected ($E$) | Duration (Weeks @ 32 EH) |
|---|:---:|:---:|:---:|:---:|:---:|
| **M1: Candidate Ingestion & Manifest v2** | 30.0 EH | 26.0 EH | 38.0 EH | **30.67 EH** | 0.95 Weeks |
| **M2: Registry Adapters & Distribution** | 32.0 EH | 28.0 EH | 40.0 EH | **32.67 EH** | 1.02 Weeks |
| **M3: Supply Chain Security (Syft/Cosign)**| 34.0 EH | 28.0 EH | 44.0 EH | **34.67 EH** | 1.08 Weeks |
| **M4: Qualification Engine & Policy** | 32.0 EH | 28.0 EH | 38.0 EH | **32.33 EH** | 1.01 Weeks |
| **M5: Promotion Engine & Two-Person Gate** | 32.0 EH | 28.0 EH | 40.0 EH | **32.67 EH** | 1.02 Weeks |
| **M6: Rollback, Retention & E2E Suite** | 28.0 EH | 24.0 EH | 34.0 EH | **28.33 EH** | 0.89 Weeks |
| **TOTAL PROGRAMME 1 PHASE A4** | **188.0 EH** | **162.0 EH** | **234.0 EH** | **191.33 EH** | **~5.98 (~6) Weeks** |

$$\text{PERT Calculation: } E = \frac{162.0 + 4(188.0) + 234.0}{6} = \frac{162.0 + 752.0 + 234.0}{6} = \frac{1148.0}{6} = \mathbf{191.33\text{ EH}}$$

---

### 5.2 Discipline Breakdown of Engineering Hours
The 188.0 nominal engineering hours are partitioned across professional disciplines:

| Discipline | Allocation (EH) | Percentage | Key Focus Areas |
|---|:---:|:---:|---|
| **Architecture & System Design** | 24.0 EH | 12.8% | Contract schemas, FSM state design, security threat models. |
| **Core Software Development** | 86.0 EH | 45.7% | Pydantic models, adapters, engines, serializers, policies. |
| **Subsystem & Pipeline Integration** | 34.0 EH | 18.1% | Jenkinsfile.release, shared library Groovy, Floci/OCI wiring. |
| **Test Suite & Failure Injection** | 24.0 EH | 12.8% | Unit tests, invalid input fuzzing, mock failures, E2E suite. |
| **Debugging & Edge-Case Remediation**| 10.0 EH | 5.3% | Windows file locking, path escaping, container race conditions. |
| **Runbooks & Documentation** | 10.0 EH | 5.3% | Cosign key runbook, rollback procedures, operational guides. |
| **TOTAL** | **188.0 EH** | **100.0%** | |

---

### 5.3 Infrastructure Resource Allocation
All engineering activities execute within strict workstation limits with zero cloud expenditure:
- **Processor**: Bounded to 4 CPU cores for compilation, container builds, and pytest execution.
- **Memory**: 8 GB Working RAM ceiling (Jenkins ~1.5 GB, Local Registry ~50 MB, Floci ~200 MB, App containers ~2.5 GB, Test runner ~1 GB).
- **Disk Storage**: 15 GB reserved workspace disk space for image layers, static tarballs, and virtual environments.
- **Cloud Expenditure**: **$0.00** (Floci-first local lab execution; zero real cloud charges).

---

## 6. Security, Governance & Architecture Conditions

The Platform Owner established six binding conditions during Gate 2 approval. Phase A4 implementation strictly adheres to and resolves each condition:

```text
+---------------------------------------------------------------------------------------------------+
|                                 RESOLVED ARCHITECTURE CONDITIONS                                  |
+---------------------------------------------------------------------------------------------------+
|  1. Container Image Integrity        --> Verified Go builder & Distroless runtime digests         |
|  2. Software Supply Chain Security   --> CycloneDX 1.5, in-toto v1.0, Cosign ECDSA P-256, runbook |
|  3. Governance Boundary              --> LOCAL_APPROVAL_SIMULATION fail-closed boundary           |
|  4. Rollback Qualification           --> Monotonic timing, Approach A (N=5) initial benchmark     |
|  5. Concurrency Bounding             --> Provisional max_workers=2 limit with measurement plan   |
|  6. Audit Ledger Test Isolation      --> CORR-ACT-AUDIT-001 tracked separately (NOT ESTIMATED)   |
+---------------------------------------------------------------------------------------------------+
```

---

### 6.1 Condition 1: Container Image Integrity & Immutable Digests
All container images must use immutable SHA-256 digests. Multi-platform index digests are strictly distinguished from platform-specific `linux/amd64` child manifest digests:

#### 1. Go Builder Image: `golang:1.27.3-alpine3.24`
- **Image Tag**: `golang:1.27.3-alpine3.24` [VERIFIED]
- **Multi-Platform Index Digest**:
  ```text
  sha256:fa3d596898d9f126af7c01d14ee7597bab3f39cccf392ef36b69fe77cd681f18
  ```
- **Platform-Specific `linux/amd64` Child Manifest Digest**:
  ```text
  sha256:0fd028db9bdd4f01657bc8047c209b04d8ce19b853d776bd6f1e76a41729b936
  ```

#### 2. Distroless Runtime Base Image: `gcr.io/distroless/static-debian12:nonroot`
- **Image Tag**: `gcr.io/distroless/static-debian12:nonroot` [VERIFIED]
- **Multi-Platform Index Digest**:
  ```text
  sha256:afa5c872c891853ca7fcf1f12c3edb23f7eeef36189728842dd51042ff57f7ab
  ```
- **Platform-Specific `linux/amd64` Child Manifest Digest**:
  ```text
  sha256:52dcfbabb7457ea47c82f6e13af8c8a4a1d9f7b0145142b3ecab20f2b888411d
  ```

*Implementation Action*: In `sample-go-service/Dockerfile`, both stages are pinned to their exact `linux/amd64` child manifest digests. No unpinned or unverified tags are permitted.

---

### 6.2 Condition 2: Software Supply Chain Security Lifecycle
Task `A4-SEC-003` fulfills the complete cryptographic key management lifecycle:
1. **Key Generation**: Local ECDSA P-256 keypair generated via `cosign generate-key-pair`.
2. **Key Encryption at Rest**: The private key (`cosign.key`) is encrypted using scrypt key derivation and AES-256-GCM. Unencrypted private keys are strictly prohibited.
3. **Passphrase Management**: Passphrase supplied via `COSIGN_PASSWORD` environment variable or retrieved from NERO `SecretManager`. Never printed to console logs or committed to Git.
4. **Filesystem Permissions**: Restricted to the runner service account (POSIX `0600`, Windows NTFS ACL deny all other users).
5. **Key Management Runbook**: Delivered under `docs/runbooks/COSIGN_KEY_MANAGEMENT_RUNBOOK.md` detailing offline backup, disaster recovery, 90-day key rotation, and compromise revocation.
6. **Offline Verification**: Signatures verify locally against `localhost:5100` without internet egress:
   ```bash
   cosign verify --key platform_core/security/keys/cosign.pub localhost:5100/<image>@sha256:<digest>
   ```

---

### 6.3 Condition 3: Governance & Two-Person Approval Boundary
The approval mechanism in `ci-cd/jenkins/pipelines/universal/Jenkinsfile` and `Jenkinsfile.release` is formally classified as:
```text
LOCAL_APPROVAL_SIMULATION
```
- **Capabilities**: Validates string inequality (`qa_approver != ops_approver`), enforces change ticket format (`CHG-*`), logs to cryptographic audit ledger, and **fails closed** if values are missing.
- **Boundary**: Does not bind to external corporate identity providers (Okta, Azure AD) or verified Jenkins session IDs. A single user can input two distinct strings.
- **Enterprise Roadmap**: Cloud phases (A5/A7/A9) will integrate Jenkins authenticated user tokens, SAML 2.0/OIDC SSO with MFA, and live ServiceNow REST change ticket verification.

---

### 6.4 Condition 4: Rollback Benchmark Protocol
The "<30 second rollback" metric is classified as an **architectural design objective**, not a production SLA. Initial qualification strictly follows **Approach A (Initial Qualification Protocol)**:
- **Sample Size**: Exactly 5 consecutive independent trials per reference application ($N = 5$).
- **Reporting Standards**: Record and report all 5 raw durations ($T_1, T_2, T_3, T_4, T_5$), the **Median** ($T_{(3)}$), and the **Maximum** ($\max(T)$). Zero P95 or P99 claims permitted for $N=5$.
- **Cache Separation**: 5 trials under **Warm Cache** (image present locally) and 5 trials under **Cold Cache** (image pulled from `localhost:5100`).
- **Timing Invariants**: Must use high-resolution monotonic clock (`time.monotonic()`). Wall-clock time recorded separately for audit ledger entries.
- **Pass Threshold**: $\text{Median} \le 30.0\text{ seconds}$ and $\text{Maximum} \le 45.0\text{ seconds}$ under Warm Cache.

---

### 6.5 Condition 5: Provisional Concurrency Bounding
Parallel build execution on local developer workstations is provisionally bounded to:
```python
max_workers = 2
```
- **Context**: Bounded as a **provisional conservative local execution limit** to prevent memory pressure or Docker container termination on 4-CPU, 8-GB workstations. It is not claimed to be a mathematically guaranteed safe ceiling.
- **Measurements Required to Increase**:
  1. Peak memory sampling (`working_set_bytes`) during multi-component builds via Windows `perfmon` / Docker stats.
  2. CPU saturation measurement (`System\Processor Queue Length`).
  3. Disk I/O throughput and space profiling during layer extraction.
  4. Memory footprints of concurrent Semgrep, Trivy, and Gitleaks scans.
  5. Workload overhead of Jenkins controller and databases.
  6. Operating system event log inspection for OOM termination or heavy paging.

---

### 6.6 Condition 6: Audit Ledger Isolation (`CORR-ACT-AUDIT-001`)
- **Status**: Tracked separately as `NOT ESTIMATED`.
- **Constraint**: It is **not** added to the A4 188.0 EH baseline without explicit Platform Owner direction.
- **Technical Scope**: Provides an environment variable override (`NERO_AUDIT_LOG_PATH`) and a global pytest autouse fixture in `tests/conftest.py` ensuring that all future automated tests write to isolated temporary directories (`tmp_path`) and never append test records to the production audit log (`platform_core/audit/audit_log.jsonl`).

---

## 7. Local Infrastructure Requirements & Verification

Before executing any A4 implementation tasks, the local development environment must satisfy the following infrastructure requirements:

```text
+---------------------------------------------------------------------------------------------------+
|                               LOCAL INFRASTRUCTURE PREREQUISITES                                  |
+---------------------------------------------------------------------------------------------------+
| Service / Component      | Port / Path              | Expected Baseline State                     |
|--------------------------|--------------------------|---------------------------------------------|
| Jenkins Controller       | localhost:8080           | Active, authenticated, JDK 17, Docker CLI   |
| Local OCI Registry       | localhost:5100           | Active, Docker Distribution v2 API healthy  |
| Floci AWS Cloud Emulator | localhost:4566           | Active, S3 bucket nero-releases-local ready  |
| PostgreSQL Primary       | localhost:5432           | Active, billing_db initialized              |
| PostgreSQL Secondary     | localhost:5434           | Active, billing_db_qa initialized           |
| Terraform State          | infrastructure/...       | Serial 23, 15 Managed Resources (INVIOLABLE)|
| Audit Ledger             | platform_core/audit/...  | 84 Records, 100% SHA-256 Valid (INVIOLABLE) |
| Git Working Branch       | devops/jenkins-floci...  | Preserved working tree, uncommitted intact  |
+---------------------------------------------------------------------------------------------------+
```

---

## 8. Comprehensive Risk Register & Mitigation Strategy

| Risk ID | Risk Description | Prob. | Impact | Mitigation Strategy | Fallback / Rollback Procedure |
|---|---|:---:|:---:|---|---|
| **RSK-A4-001** | Workstation memory exhaustion during concurrent builds | Medium | High | Enforce `max_workers = 2`. Profile memory before parallel execution. | Immediately throttle to `max_workers = 1`. Free unused container memory. |
| **RSK-A4-002** | Local OCI registry (`:5100`) tag overwrite | Low | High | Implement client-side tag immutability check in `OCIRegistryAdapter`. | Query image digest before push; abort if tag exists with differing digest. |
| **RSK-A4-003** | Cosign private key exposure or passphrase leak | Low | Critical | Encrypt private key with AES-256-GCM; inject passphrase via `SecretManager`. | Immediately execute `COSIGN_KEY_MANAGEMENT_RUNBOOK.md` compromise revocation. |
| **RSK-A4-004** | Floci S3 endpoint transient disconnection | Low | Medium | Implement exponential backoff retry (3 attempts) in `S3ReleaseAdapter`. | Cache static bundles locally; retry upload before failing qualification. |
| **RSK-A4-005** | Audit ledger file-locking contention | Low | Medium | Reuses existing atomic cross-platform file locking (`msvcrt` / `fcntl`). | Queue audit records in-memory and retry write with jitter. |
| **RSK-A4-006** | Multi-component distribution partial upload failure | Medium | High | Atomic distribution dispatcher: all components must succeed or all are rolled back. | Delete uploaded registry tags and S3 objects; mark release `REJECTED`. |
| **RSK-A4-007** | Cold-cache image pull exceeds 30-second target | Medium | Low | Clarify $<30$s as architectural design target; report raw durations for $N=5$. | Pre-warm local container daemon cache for high-priority production services. |
| **RSK-A4-008** | Inadvertent modification of Terraform state Serial 23 | Low | Critical | Strictly read-only policy on `infrastructure/terraform/`. No `terraform apply`. | Inviolable rule: Terraform state is never touched during Phase A4 release tasks. |

---

## 9. First Implementation Session Plan (Task A4-CAN-001)

When the Platform Owner authorizes Gate 3, implementation begins with a small, self-contained, and independently verifiable task. This section details the complete execution blueprint for that first session.

```text
+===================================================================================================+
|                              FIRST IMPLEMENTATION SESSION BLUEPRINT                               |
+===================================================================================================+
|  Task ID:           A4-CAN-001                                                                    |
|  Task Name:         Candidate Release Contract Model                                              |
|  Subsystem:         platform_core/models/candidate_contract.py                                    |
|  Nominal Estimate:  8.0 Engineering Hours                                                         |
|  Safety Posture:    100% Isolated Pure Python Model (Zero Risk to Running Infrastructure)         |
+===================================================================================================+
```

### 9.1 Purpose & Scope
The purpose of Task `A4-CAN-001` is to create the formal Pydantic v2 data models that define what a "candidate release" is. It ingests the raw evidence generated by the Phase A3 CI pipeline (`ci_evidence.json`), parses it, and strictly validates that:
1. Every component has a valid 64-character SHA-256 digest.
2. The Git commit SHA is a valid 40-character hexadecimal string.
3. Automated test pass rate is 100% (zero failures, zero errors).
4. Code coverage meets or exceeds the mandatory 80.0% diff coverage threshold.
5. Release tags adhere to Semantic Versioning (`vMAJOR.MINOR.PATCH`).

### 9.2 Files Expected to Change
- **Created**:
  - `platform_core/models/candidate_contract.py` (New typed Pydantic v2 model file).
  - `tests/unit/test_candidate_contract.py` (Comprehensive unit test suite).
- **Modified**:
  - None. (Zero existing application code, pipelines, or infrastructure files are touched).

### 9.3 Prerequisites
- Python 3.12 virtual environment active.
- Pydantic v2 available.
- Existing `platform_core/engine/ci_evidence.py` inspected for schema compatibility.

### 9.4 Implementation Sequence
1. Create `platform_core/models/` directory (if not present).
2. Implement child models:
   - `ComponentArtifact`: Validates component name, artifact type (`oci_image` or `static_tarball`), repository path, tag, and SHA-256 digest regex (`^sha256:[a-f0-9]{64}$`).
   - `TestEvidenceSummary`: Validates total tests, passed count, failed count, skipped count, and duration.
   - `DiffCoverageEvidence`: Validates changed lines, covered lines, and percentage ($\ge 80.0\%$).
   - `SecurityScanEvidence`: Validates vulnerability counts, secret scan status, and active exception IDs.
3. Implement root model `CandidateReleaseContract`:
   - Validates release ID, application ID, Git metadata, execution ID, and component dictionary.
   - Adds `@model_validator(mode='after')` enforcing:
     - All tests must pass (`failed == 0` and `errors == 0`).
     - Diff coverage must be $\ge 80.0\%$.
     - At least one valid component must be present.
4. Author unit test suite `tests/unit/test_candidate_contract.py` covering:
   - Successful parsing of compliant CI evidence payload.
   - Rejection of invalid / truncated SHA-256 hashes.
   - Rejection of contracts with failing unit tests.
   - Rejection of contracts with diff coverage $< 80.0\%$.
   - Serialization to and from JSON.

### 9.5 Test Strategy & Acceptance Criteria
- **Execution**: Run pytest exclusively on the new unit test file:
  ```powershell
  pytest tests/unit/test_candidate_contract.py -v
  ```
- **Acceptance Criteria**:
  - 100% of unit tests pass with zero warnings.
  - Zero modifications to existing files.
  - Zero audit records appended.
  - Zero Docker or Terraform commands executed.

---

## 10. Verification & Acceptance Checklist

To provide clear operational checkpoints throughout Phase A4, each milestone must satisfy its formal acceptance gate before the next milestone may begin:

```text
+===================================================================================================+
|                                MILESTONE ACCEPTANCE GATE CHECKLIST                                |
+===================================================================================================+
| Milestone 1: Candidate Ingestion & Manifest v2 (30.0 EH)                                          |
|   [ ] A4-CAN-001: Pydantic v2 CandidateReleaseContract validates digests, tests, and coverage.     |
|   [ ] A4-CAN-002: Ingestion engine verifies Git commit SHA against catalog authorization.        |
|   [ ] A4-MAN-001: ReleaseManifestV2 model serializes multi-component specifications.             |
|   [ ] A4-MAN-002: Manifest serializer computes deterministic payload SHA-256 hash.               |
|                                                                                                   |
| Milestone 2: Registry Adapters & Distribution (32.0 EH)                                           |
|   [ ] A4-REG-001: BaseRegistryAdapter interface defines standard registry contract.               |
|   [ ] A4-REG-002: OCI adapter pushes to localhost:5100 and enforces client-side tag immutability. |
|   [ ] A4-REG-003: S3 adapter uploads static frontend tarballs to Floci with SHA-256 verification. |
|   [ ] A4-REG-004: Distribution dispatcher executes atomic multi-component push with fail-closed.  |
|                                                                                                   |
| Milestone 3: Software Supply Chain Security (34.0 EH)                                             |
|   [ ] A4-SEC-001: Syft adapter emits CycloneDX 1.5 JSON SBOMs for containers and directories.     |
|   [ ] A4-SEC-002: Provenance adapter emits in-toto v1.0 build attestation linking Git and builder. |
|   [ ] A4-SEC-003: Cosign signs images; delivers docs/runbooks/COSIGN_KEY_MANAGEMENT_RUNBOOK.md.    |
|   [ ] A4-SEC-004: Supply chain aggregator binds digests, SBOMs, provenance, and signatures.       |
|                                                                                                   |
| Milestone 4: Release Qualification Engine & Policy (32.0 EH)                                      |
|   [ ] A4-QLF-001: 12-Step checklist evaluates all qualification criteria deterministically.       |
|   [ ] A4-QLF-002: Release FSM enforces legal state transitions and blocks illegal promotions.     |
|   [ ] A4-QLF-003: Security policy validator asserts zero unexempted HIGH/CRITICAL CVEs.           |
|   [ ] A4-QLF-004: Audit logger appends tamper-evident RELEASE_QUALIFIED events under file locking.|
|                                                                                                   |
| Milestone 5: Promotion Engine & Two-Person Gate (32.0 EH)                                         |
|   [ ] A4-PRM-001: Zero-rebuild promotion engine deploys identical digests across environments.     |
|   [ ] A4-PRM-002: Two-person gate enforces distinct identities and CHG-* ticket; fails closed.    |
|   [ ] A4-PRM-003: Dedicated Jenkinsfile.release pipeline executes multi-stage release flow.       |
|   [ ] A4-PRM-004: neroRelease.groovy trusted shared library steps pass CPS transformation.        |
|                                                                                                   |
| Milestone 6: Rollback, Retention, Revocation & E2E Suite (28.0 EH)                                |
|   [ ] A4-ROL-001: Rollback orchestrator restores previous manifest; benchmarked via Approach A.   |
|   [ ] A4-RET-001: Retention sweeper purges orphaned tags while protecting active rollback images. |
|   [ ] A4-REV-001: Revocation coordinator halts compromised releases and records audit alert.      |
|   [ ] A4-TST-001: E2E suite passes 100% across all 4 reference applications and failure cases.    |
+===================================================================================================+
```

---

## 11. Platform Owner Stop/Go Authorization Checklist (Gate 3)

Before granting Gate 3 authorization, the Platform Owner should review this definitive Stop/Go Authorization Checklist:

| Question for Platform Owner | Platform Engineering Guarantee | Status |
|---|---|:---:|
| **1. What engineering work will begin?** | Milestone 1, starting strictly with Task `A4-CAN-001` (pure Python Pydantic contract model). | Confirmed |
| **2. What files could change initially?** | Only new model and test files (`platform_core/models/candidate_contract.py` and `tests/unit/...`). | Confirmed |
| **3. Which existing services will be used?** | Jenkins, Floci, and local OCI registry are accessed read-only for verification. No restarts or reconfigurations. | Confirmed |
| **4. What critical data is protected?** | Terraform state Serial 23 (15 managed resources) and Audit Ledger (84 records) are inviolable. | Confirmed |
| **5. What could go wrong?** | Unit tests fail or encounter syntax issues. Zero platform or container risk. | Confirmed |
| **6. How do we recover from failures?** | Immediate rollback: delete or correct the new Python file. No system state is polluted. | Confirmed |
| **7. Which actions remain strictly PROHIBITED?** | No real AWS credentials, no cloud provisioning, no Git commits/pushes, no Terraform state changes. | Confirmed |
| **8. How will progress be reported?** | Formal milestone completion summaries with test evidence packages delivered at each milestone boundary. | Confirmed |

---

## 12. Plain-Language Summary for the Platform Owner

### What You Are Authorizing by Approving Gate 3
Approving **Gate 3 (Implementation Authorization)** means granting the engineering team permission to begin writing the software code for Phase A4 in the local repository, starting with Milestone 1.

Specifically, approving Gate 3 means:
1. **You are authorizing local software engineering**: The team will create the Python models, storage adapters, supply-chain signing tools, and Jenkins pipeline files described in the 24-task plan.
2. **You are NOT spending any money**: All work takes place on the local developer workstation using local Docker containers and the Floci cloud emulator. Cloud expenditure remains strictly **$0.00**.
3. **You are NOT altering live infrastructure**: Existing running containers (Jenkins, Postgres, Floci, OCI registry) will not be deleted, recreated, or reconfigured. The Terraform state remains frozen at Serial 23.
4. **You are NOT modifying Git history**: All work remains on the working tree of the `devops/jenkins-floci-local-lab` branch without running `git commit` or `git push`.
5. **You retain complete control at every milestone**: Work proceeds milestone by milestone. You will receive an evidence-backed verification report after each milestone before the next begins.

### Current Implementation Posture
Until you issue explicit authorization for Gate 3, **all engineering work remains strictly halted**. The platform is fully prepared, verified, and standing by for your command.

---
*End of Report — NERO-A4-KICKOFF-PLAN-001*
