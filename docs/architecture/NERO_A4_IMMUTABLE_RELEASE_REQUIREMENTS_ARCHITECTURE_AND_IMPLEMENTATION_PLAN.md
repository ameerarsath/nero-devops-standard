# NERO Universal Enterprise DevOps Automation Platform
# Programme 1 — Phase A4: Immutable Release Engineering & Artifact Repository Integration
## Requirements, Architecture & Engineering Implementation Plan

**Document Type:** Formal Requirements, Architecture & Engineering Implementation Plan  
**Document ID:** NERO-A4-PLAN-001  
**Programme:** NERO Programme 1 — Deterministic DevOps Automation First  
**Phase:** Phase A4 — Immutable Release Engineering & Artifact Repository Integration  
**Status:** **`PROPOSED_AWAITING_OWNER_AUTHORIZATION`** (Planning Complete; Implementation Halted)  
**Effective Date:** 2026-11-08  
**Author:** NERO Senior Platform Engineer, Release Engineering Architect & DevSecOps Engineer  
**Reference Baseline:** NERO A3 Completion (139/139 Tests Passed, Serial 23 State, 82 Chained Audit Records)  

---

## 1. Executive Summary & Product Vision

### The Core Principle: Build Once, Promote Everywhere
Software delivery pipelines often suffer from subtle defects, environment divergence, and security vulnerabilities caused by rebuilding code in each target environment. Compiling Java bytecode, packaging Node.js bundles, or building container images separately in QA and Production introduces unverified dependency variations, volatile compiler timestamps, and uncontrolled runtime mutations.

**NERO Phase A4** eliminates this failure mode by operationalizing **ADR-003 (Immutable Release Packaging & Zero-Rebuild Promotion)**:
> **"Build once. Qualify once. Create an immutable release. Promote the exact same artifact through environments without rebuilding."**

Phase A4 establishes the formal boundary between Continuous Integration (A3) and Release Engineering (A4):
- **Phase A3 (Continuous Integration)**: Validates source code commits and pull requests, runs unit/integration tests, enforces changed-code diff-coverage gates ($\ge 80\%$), executes DevSecOps scans (Gitleaks, Semgrep, Trivy), and outputs canonical `ci_evidence.json` alongside candidate build digests.
- **Phase A4 (Immutable Release Engineering)**: Ingests verified CI candidate outputs, applies the 12-Step Release Qualification Checklist, mints the **Universal Immutable Release Manifest v2**, publishes multi-component container images to the local private OCI registry (`localhost:5100`), generates CycloneDX SBOMs and in-toto provenance, applies Cosign digital signatures, and orchestrates zero-rebuild promotions across environments (`develop` $\rightarrow$ `qa` $\rightarrow$ `staging` $\rightarrow$ `prod`) with authenticated two-person production governance and deterministic rollback.

### The 10 Fundamental Release Engineering Questions
A4 provides definitive, cryptographically verifiable answers to the 10 core release engineering questions:
1. **What exactly is being released?** The multi-component application specification and artifacts defined in the immutable `release-manifest.json`.
2. **Where did the artifact originate?** The source Git repository, commit SHA, and branch captured in the candidate contract.
3. **Was it built by a trusted process?** The Jenkins CI execution ID and cryptographic build provenance attestation.
4. **Has its integrity been verified?** Full 64-character SHA-256 layer and image digests matching between registry and manifest.
5. **Is its software inventory available?** The complete CycloneDX 1.5 JSON Software Bill of Materials (SBOM).
6. **Has the artifact been signed?** Signed locally via Cosign using the platform's trusted keypair.
7. **Can its signature be independently verified?** Verified offline using `cosign verify` and the public key `cosign.pub`.
8. **Which environments have approved it?** Recorded in the manifest's immutable promotion history and audit ledger.
9. **Can the release be promoted without rebuilding?** Yes; target environments pull the exact pinned SHA-256 digest with zero recompilation.
10. **Can the exact release be restored during rollback?** Yes; rollback redeploys the prior immutable release manifest in under 30 seconds.

---

## 2. CI-to-Release Qualification Boundary & Candidate Release Contract

The interface between Phase A3 and Phase A4 is governed by a strict, typed contract:

```text
+---------------------------------------------------------------------------------------------------+
|                              CI-TO-RELEASE BOUNDARY & QUALIFICATION FLOW                          |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|    +-----------------------------+                                                                |
|    |      Phase A3 Output        |                                                                |
|    |     (ci_evidence.json)      |                                                                |
|    +--------------+--------------+                                                                |
|                   |                                                                               |
|                   v                                                                               |
|    +-----------------------------+                                                                |
|    |  Candidate Release Contract | ----> Validates: Full Digests, Test Pass, >=80% Diff Coverage, |
|    |     (Candidate Ingestion)   |                  Zero Blocker CVEs, Catalog Authorization      |
|    +--------------+--------------+                                                                |
|                   |                                                                               |
|          [Validation Passes]                                                                      |
|                   |                                                                               |
|                   v                                                                               |
|    +-----------------------------+                                                                |
|    |  Release Qualification      | ----> 12-Step Release Checklist, CycloneDX SBOM,               |
|    |  Engine (Phase A4 Core)     |       in-toto Provenance, Cosign Signature, OCI Push           |
|    +--------------+--------------+                                                                |
|                   |                                                                               |
|                   v                                                                               |
|    +-----------------------------+                                                                |
|    |   Immutable Release         | ----> release-manifest.json v2.0.0                             |
|    |   Manifest Minted           |       Appended to audit_log.jsonl                              |
|    +-----------------------------+                                                                |
+---------------------------------------------------------------------------------------------------+
```

### Typed Candidate Release Contract Model
The Candidate Release Contract model guarantees that an unverified CI run can never produce a release:

```python
"""
NERO Universal Enterprise DevOps Automation Platform
Candidate Release Contract Model (A4-REL-001)
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, field_validator


class CandidateComponent(BaseModel):
    name: str = Field(description="Component name, e.g. 'backend', 'frontend', 'api'")
    type: str = Field(description="Artifact type, e.g. 'container_image', 'static_bundle'")
    runtime_version: str = Field(description="Runtime version, e.g. '1.27.3', '17', '22'")
    build_adapter: str = Field(description="Build adapter used, e.g. 'dockerfile', 'node', 'go'")
    artifact_reference: str = Field(description="Repository or bundle reference")
    digest: str = Field(description="Canonical sha256:64-char-hex digest")

    @field_validator("digest")
    def validate_digest_format(cls, v):
        if not v.startswith("sha256:") or len(v[7:]) != 64:
            raise ValueError(f"Invalid artifact digest format: '{v}' (must be sha256:<64-hex>)")
        return v


class CandidateReleaseContract(BaseModel):
    """Authoritative contract ingested from Phase A3 CI outputs."""
    contract_version: str = Field(default="1.0.0")
    application_id: str = Field(description="Application ID registered in catalog")
    spec_version: str = Field(description="Application specification version")
    repository: str = Field(description="Git repository URL")
    commit_sha: str = Field(description="Full 40-character Git commit hash")
    branch: str = Field(description="Source Git branch")
    ci_execution_id: str = Field(description="Unique Jenkins execution ID")
    ci_build_number: int = Field(description="Jenkins build number")
    ci_result: str = Field(description="SUCCESS, FAILURE, UNSTABLE")
    components: List[CandidateComponent] = Field(description="List of built components")
    test_total: int
    test_passed: int
    test_failed: int
    coverage_diff_percentage: float = Field(description="Line coverage on changed code")
    secrets_detected: int = Field(default=0)
    sast_blockers: int = Field(default=0)
    cve_critical: int = Field(default=0)
    cve_high: int = Field(default=0)
    exemptions_applied: int = Field(default=0)
    ci_evidence_checksum: str = Field(description="SHA-256 of ci_evidence.json")
    created_at: str

    def is_eligible_for_release(self) -> (bool, List[str]):
        """Evaluates absolute eligibility criteria."""
        reasons = []
        if self.ci_result != "SUCCESS":
            reasons.append(f"CI execution status is '{self.ci_result}', expected 'SUCCESS'")
        if self.test_failed > 0:
            reasons.append(f"CI had {self.test_failed} failed tests")
        if self.coverage_diff_percentage < 80.0:
            reasons.append(f"Diff coverage {self.coverage_diff_percentage}% is below 80.0% threshold")
        if self.secrets_detected > 0:
            reasons.append(f"Detected {self.secrets_detected} unexempted secrets")
        if self.sast_blockers > 0:
            reasons.append(f"Detected {self.sast_blockers} blocking SAST vulnerabilities")
        if self.cve_critical > 0 or self.cve_high > 0:
            reasons.append(f"Detected {self.cve_critical} CRITICAL and {self.cve_high} HIGH CVEs")
        if not self.components:
            reasons.append("Zero components provided in candidate release")
        return len(reasons) == 0, reasons
```

---

## 3. Universal Immutable Release Manifest Schema v2

Phase A4 introduces the **Universal Immutable Release Manifest Schema v2 (`ReleaseManifestV2`)**, evolving the preliminary schema from Phase A1 into a comprehensive, multi-component, multi-environment specification:

```yaml
apiVersion: platform.nero/v2
kind: ReleaseManifest

metadata:
  releaseId: "rel-20261108193000-hotel-billing"
  applicationId: "hotel-billing"
  version: "1.0.0"
  createdAt: "2026-11-08T19:30:00Z"
  releasedBy: "jenkins-ci@trusted-agent"
  status: "QUALIFIED" # CANDIDATE, QUALIFIED, REJECTED, PROMOTION_PENDING, PROMOTED, SUPERSEDED, REVOKED

source:
  repository: "https://github.com/ameerarsath/billing-system.git"
  commitSha: "a9482b810fc7d23a17e889b940982cf61a4982a1"
  branch: "develop"
  tag: "v1.0.0-rc1"

ci:
  executionId: "ci-hotel-billing-1731094200-b42"
  jobName: "universal-ci-pipeline"
  buildNumber: 42
  evidenceChecksum: "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

components:
  backend:
    name: "backend"
    type: "oci_container_image"
    repository: "localhost:5100/hotel-billing-backend"
    tag: "1.0.0"
    digest: "sha256:4f8a91c83a7493a7e3052846194a82b947265819385927491029485726194829"
    sbom:
      format: "CycloneDX-1.5-JSON"
      reference: "sbom/hotel-billing-backend-1.0.0.json"
      sha256: "sha256:7b92019482910482947192840192840192840192840192840192840192840192"
    provenance:
      format: "in-toto-v1.0"
      reference: "provenance/hotel-billing-backend-1.0.0.json"
      sha256: "sha256:9182736451928374650192837465019283746501928374650192837465019283"
    signature:
      format: "cosign"
      reference: "localhost:5100/hotel-billing-backend:sha256-4f8a91c83a7493a7e3052846194a82b947265819385927491029485726194829.sig"
      publicKeyId: "cosign-local-root-2026"

  frontend:
    name: "frontend"
    type: "static_tarball"
    artifactPath: "releases/hotel-billing/rel-20261108193000/hotel-billing-frontend-1.0.0.tar.gz"
    sha256: "sha256:d829104829104829104829104829104829104829104829104829104829104829"
    sizeBytes: 1459204
    sbom:
      format: "CycloneDX-1.5-JSON"
      reference: "sbom/hotel-billing-frontend-1.0.0.json"
      sha256: "sha256:1029384756102938475610293847561029384756102938475610293847561029"

qualification:
  summary: "PASSED"
  checksEvaluated: 12
  checksPassed: 12
  diffCoverage: 100.0
  securityVulnerabilities: 0
  qualifiedAt: "2026-11-08T19:30:15Z"
  policyVersion: "2026.1"

promotions:
  - environment: "develop"
    promotedAt: "2026-11-08T19:30:30Z"
    promotedBy: "jenkins-ci@trusted-agent"
    approver: "auto-ci"
    changeTicket: "N/A"
    digestVerified: true
    status: "PROMOTED"

signatures:
  manifestSignature: "MEQCID...[ECDSA-P256-SIG]..."
  publicKey: "cosign-local-root-2026"
```

---

## 4. Release Qualification Engine & Finite State Machine

The Release Qualification Engine evaluates releases against a deterministic **12-Step Release Qualification Checklist**:

```text
========================================================================================
                      12-STEP RELEASE QUALIFICATION CHECKLIST
========================================================================================
  [Step 1]  Candidate Contract Validity   : Ingested contract schema and checksum valid
  [Step 2]  Catalog & Branch Clearance    : App ID in catalog; branch allowed for release
  [Step 3]  Git Commit Non-Repudiation    : Commit exists on origin; no uncommitted drift
  [Step 4]  Artifact Presence in Registry : All component images confirmed in registry
  [Step 5]  Cryptographic Digest Parity   : Manifest digest matches remote registry digest
  [Step 6]  CycloneDX SBOM Completeness   : Valid JSON schema; packages enumerated
  [Step 7]  In-Toto Provenance Validity   : Hermetic builder identity and inputs matched
  [Step 8]  Digital Signature Verification: Cosign signature verified via public key
  [Step 9]  Security Gate Enforcement     : 0 unexempted CVEs, 0 secrets, 0 SAST blockers
  [Step 10] Diff-Coverage Gate Assertion  : Changed-code diff coverage >= 80.0%
  [Step 11] Environment Compatibility     : Ports, memory, CPU fit target infrastructure
  [Step 12] Rollback Plan Readiness       : Prior release identified; schema non-breaking
========================================================================================
```

### Release State Machine (FSM)
Releases transition through strictly validated states:

```text
+---------------------------------------------------------------------------------------------------+
|                                  RELEASE FINITE STATE MACHINE                                     |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|               [CI Ingestion]                                                                      |
|                     |                                                                             |
|                     v                                                                             |
|               +-------------+                                                                     |
|               |  CANDIDATE  |                                                                     |
|               +------+------+                                                                     |
|                      |                                                                            |
|        +-------------+-------------+                                                              |
|        |                           |                                                              |
|   [Checks Pass]              [Check Fails]                                                        |
|        |                           |                                                              |
|        v                           v                                                              |
|  +-----------+               +------------+                                                       |
|  | QUALIFIED |               |  REJECTED  | (Terminal State)                                      |
|  +-----+-----+               +------------+                                                       |
|        |                                                                                          |
|        v                                                                                          |
|  +-------------------+                                                                            |
|  | PROMOTION_PENDING | <-------------------+                                                      |
|  +-----+-------------+                     |                                                      |
|        |                                   |                                                      |
|  [Approvals Granted]             [Promote to Next Env]                                            |
|        |                                   |                                                      |
|        v                                   |                                                      |
|  +-----------+                             |                                                      |
|  |  PROMOTED | ----------------------------+                                                      |
|  +-----+-----+                                                                                    |
|        |                                                                                          |
|  [New Release Deployed]                                                                           |
|        |                                                                                          |
|        v                                                                                          |
|  +------------+                                                                                   |
|  | SUPERSEDED | (Historic Rollback Target)                                                        |
|  +------------+                                                                                   |
|        |                                                                                          |
|  [Vulnerability Discovered]                                                                       |
|        |                                                                                          |
|        v                                                                                          |
|  +-----------+                                                                                    |
|  |  REVOKED  | (Terminal Security Blockade)                                                       |
|  +-----------+                                                                                    |
+---------------------------------------------------------------------------------------------------+
```

---

## 5. Software Supply Chain Security Architecture

Phase A4 establishes an unbroken, tamper-evident software supply chain aligning with **SLSA Level 3**:

```text
+---------------------------------------------------------------------------------------------------+
|                                  NERO SUPPLY CHAIN EVIDENCE CHAIN                                 |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|    Git Commit (SHA)                                                                               |
|         |                                                                                         |
|         v                                                                                         |
|    Hermetic Build (Jenkins Isolated Agent)                                                        |
|         |                                                                                         |
|         +---> Pinned SHA-256 Digest (image@sha256:...)                                            |
|         |                                                                                         |
|         +---> CycloneDX 1.5 JSON SBOM (syft packages)                                             |
|         |                                                                                         |
|         +---> In-Toto v1.0 Provenance Attestation (slsa-predicate)                                 |
|         |                                                                                         |
|         +---> Cosign Cryptographic Signature (cosign sign --key)                                  |
|         |                                                                                         |
|         v                                                                                         |
|    Universal Release Manifest v2 (Payload Checksummed)                                            |
|         |                                                                                         |
|         v                                                                                         |
|    Immutable Audit Ledger (audit_log.jsonl SHA-256 Chained)                                       |
+---------------------------------------------------------------------------------------------------+
```

### Local Cosign Architecture (Zero Cloud KMS Spend)
To maintain the platform's strict \$0.00 cloud spend mandate:
1. **Key Generation**: Local ECDSA P-256 keypair generated via `cosign generate-key-pair`.
2. **Key Storage**:
   - `cosign.pub`: Committed to `platform_core/security/keys/cosign.pub` for open verification.
   - `cosign.key`: Encrypted at rest. Passphrase stored securely in NERO `SecretManager`.
3. **Signing Mechanism**:
   - Signatures are uploaded to the local OCI registry as standard OCI artifacts attached to the image digest (`localhost:5100/<image>:sha256-<digest>.sig`).

---

## 6. Jenkins Pipeline Architecture for Release Engineering

Continuous Integration and Release Engineering are decoupled into two distinct, dedicated Jenkins pipelines:

```text
+---------------------------------------------------------------------------------------------------+
|                                 JENKINS PIPELINE DECOUPLING                                       |
+---------------------------------------------------------------------------------------------------+
|  Jenkinsfile.ci (A3 CI Pipeline)             |  Jenkinsfile.release (A4 Release Pipeline)         |
|  Trigger: SCM Webhook (Push / PR)            |  Trigger: Successful CI or Manual Promotion        |
|  Stage 1: Preflight & Catalog Check          |  Stage 1: Candidate Ingestion & Contract Check     |
|  Stage 2: Secret Scanning (Gitleaks)         |  Stage 2: Artifact Distribution (OCI Push / S3)    |
|  Stage 3: Parallel Multi-Component Build     |  Stage 3: CycloneDX SBOM & in-toto Provenance      |
|  Stage 4: Automated Testing & JUnit Parsing  |  Stage 4: Cosign Digital Signing                   |
|  Stage 5: Code Quality & 80% Diff Coverage   |  Stage 5: 12-Step Release Qualification Checklist  |
|  Stage 6: SAST & SCA Scans (Semgrep, Trivy)  |  Stage 6: Mint Universal Release Manifest v2       |
|  Stage 7: Intermediate CI Evidence Emission  |  Stage 7: Release Catalog Registration & Audit Log |
|                                              |  Stage 8: Environment Promotion (Zero Rebuild)     |
+---------------------------------------------------------------------------------------------------+
```

---

## 7. Platform Core Subsystem Architecture

To implement Phase A4, the `platform_core` package is expanded with the following dedicated, typed modules:

```text
platform_core/
├── adapters/
│   ├── registry/
│   │   ├── base.py                 # Abstract BaseRegistryAdapter interface
│   │   ├── oci_adapter.py          # Expanded OCI Distribution v2 adapter
│   │   └── s3_release_adapter.py   # S3/Floci static release adapter
│   └── security/
│       ├── cosign_adapter.py       # Cosign CLI signing and verification adapter
│       └── syft_adapter.py         # Syft SBOM generation adapter
├── engine/
│   ├── candidate_ingest.py         # Candidate contract parser and validator
│   ├── release_qualification.py    # 12-step qualification checklist & FSM
│   ├── release_manifest.py         # Manifest v2 generator and serializer
│   ├── promotion_engine.py         # Zero-rebuild promotion coordinator
│   └── rollback_engine.py          # 10-step rollback orchestrator
├── models/
│   ├── candidate_contract.py       # Pydantic v2 candidate release models
│   └── release_manifest_v2.py      # Pydantic v2 ReleaseManifest models
└── policy/
    ├── retention_policy.py         # Release retention and sweeper logic
    └── revocation_policy.py        # Release revocation enforcement
```

---

## 8. Detailed Work Breakdown Structure (24 Tasks Across 6 Milestones)

The engineering implementation of Phase A4 is partitioned into 24 discrete tasks:

### Milestone 1: Candidate Ingestion & Release Manifest Architecture (30.0 EH)
- **A4-CAN-001: Candidate Release Contract Model** (8.0 EH)
  - *Subsystem*: `platform_core/models/candidate_contract.py`
  - *Objective*: Implement Pydantic v2 contract validating CI outputs, test evidence, diff coverage, and digests.
  - *Dependencies*: A3-EVN-001 (`ci_evidence.py`).
  - *Acceptance*: Rejects contracts with unpinned digests, failing tests, or diff coverage $<80\%$.
- **A4-CAN-002: Candidate Ingestion & Preflight Validator** (8.0 EH)
  - *Subsystem*: `platform_core/engine/candidate_ingest.py`
  - *Objective*: Parse `ci_evidence.json`, inspect catalog authorization, and verify origin commit SHA.
  - *Dependencies*: A4-CAN-001.
  - *Acceptance*: Rejects unapproved repositories or branches with `CandidateEligibilityError`.
- **A4-MAN-001: Universal Release Manifest v2 Schema** (8.0 EH)
  - *Subsystem*: `platform_core/models/release_manifest_v2.py`
  - *Objective*: Formal Pydantic v2 model supporting multi-component OCI images, tarballs, SBOMs, signatures, and promotions.
  - *Dependencies*: Existing `release_manager.py`.
  - *Acceptance*: Full cryptographic serialization and schema validation.
- **A4-MAN-002: Manifest Serializer & Catalog Registrar** (6.0 EH)
  - *Subsystem*: `platform_core/engine/release_manifest.py`
  - *Objective*: Mint immutable manifests, calculate payload checksums, and store in `.nero_manifests/` and S3.
  - *Dependencies*: A4-MAN-001.
  - *Acceptance*: Verifies manifest payload hash matches catalog entry byte-for-byte.

### Milestone 2: Registry Adapter Expansion & Multi-Artifact Distribution (32.0 EH)
- **A4-REG-001: BaseRegistryAdapter Interface** (6.0 EH)
  - *Subsystem*: `platform_core/adapters/registry/base.py`
  - *Objective*: Define abstract interface for `publish_image`, `retrieve_manifest`, `verify_digest`, and `apply_retention`.
  - *Dependencies*: `platform_core/adapters/base.py`.
  - *Acceptance*: Fully typed request/response contracts and normalized error hierarchy.
- **A4-REG-002: Expanded OCI Distribution Adapter** (10.0 EH)
  - *Subsystem*: `platform_core/adapters/registry/oci_adapter.py`
  - *Objective*: Support client-side tag immutability, manifest list queries, and OCI artifact upload against `localhost:5100`.
  - *Dependencies*: A4-REG-001.
  - *Acceptance*: Pushes images, rejects tag overwrite attempts, and retrieves canonical 64-char digests.
- **A4-REG-003: S3 Static Artifact Release Adapter** (8.0 EH)
  - *Subsystem*: `platform_core/adapters/registry/s3_release_adapter.py`
  - *Objective*: Package and publish static frontend tarballs to Floci S3 with SHA-256 validation.
  - *Dependencies*: A4-REG-001.
  - *Acceptance*: Publishes frontend tarball, verifies checksum, and supports zero-rebuild retrieval.
- **A4-REG-004: Multi-Component Distribution Dispatcher** (8.0 EH)
  - *Subsystem*: `platform_core/engine/distribution_dispatcher.py`
  - *Objective*: Concurrently distribute container images to OCI registry and static assets to S3.
  - *Dependencies*: A4-REG-002, A4-REG-003.
  - *Acceptance*: Atomic multi-component distribution; fails closed if any component upload fails.

### Milestone 3: Software Supply Chain Security — Syft & Cosign (34.0 EH)
- **A4-SEC-001: Syft SBOM Generation Adapter** (10.0 EH)
  - *Subsystem*: `platform_core/adapters/security/syft_adapter.py`
  - *Objective*: Generate CycloneDX 1.5 JSON SBOMs for container images and filesystem directories.
  - *Dependencies*: External Syft binary / fallback cataloger.
  - *Acceptance*: Emits valid CycloneDX JSON with full package dependencies and licenses.
- **A4-SEC-002: In-Toto Build Provenance Attestation** (8.0 EH)
  - *Subsystem*: `platform_core/adapters/security/provenance_adapter.py`
  - *Objective*: Generate SLSA-compliant in-toto v1.0 provenance attestation linking builder identity to git commit.
  - *Dependencies*: A4-MAN-001.
  - *Acceptance*: Emits predicate capturing builder environment, git commit, and artifact digests.
- **A4-SEC-003: Cosign Digital Signing Adapter** (10.0 EH)
  - *Subsystem*: `platform_core/adapters/security/cosign_adapter.py`
  - *Objective*: Sign container images and release manifests using local ECDSA P-256 keypair.
  - *Dependencies*: Local Cosign CLI / cryptographic fallback.
  - *Acceptance*: Attaches detached signature to registry; verifies signature using `cosign.pub`.
- **A4-SEC-004: Supply Chain Evidence Aggregator** (6.0 EH)
  - *Subsystem*: `platform_core/engine/supply_chain_aggregator.py`
  - *Objective*: Bind image digest, SBOM, provenance, and signature into manifest metadata.
  - *Dependencies*: A4-SEC-001, A4-SEC-002, A4-SEC-003.
  - *Acceptance*: Complete evidence graph verified in candidate release contract.

### Milestone 4: Release Qualification Engine & Policy Gates (32.0 EH)
- **A4-QLF-001: 12-Step Release Qualification Engine** (10.0 EH)
  - *Subsystem*: `platform_core/engine/release_qualification.py`
  - *Objective*: Implement the 12-Step Release Qualification Checklist.
  - *Dependencies*: Milestones 1, 2, 3.
  - *Acceptance*: Validates all 12 criteria; returns structured pass/fail report with triage details.
- **A4-QLF-002: Release Finite State Machine (FSM)** (8.0 EH)
  - *Subsystem*: `platform_core/engine/release_fsm.py`
  - *Objective*: Enforce legal state transitions (`CANDIDATE` $\rightarrow$ `QUALIFIED` $\rightarrow$ `PROMOTED` $\rightarrow$ `SUPERSEDED` / `REVOKED`).
  - *Dependencies*: A4-QLF-001.
  - *Acceptance*: Blocks illegal transitions (e.g. promoting `REJECTED` or `REVOKED` releases).
- **A4-QLF-003: Release Security Policy Validator** (8.0 EH)
  - *Subsystem*: `platform_core/policy/release_policy.py`
  - *Objective*: Assert zero unexempted security blocker findings and verify security tier compliance.
  - *Dependencies*: Existing `security_exceptions.py`.
  - *Acceptance*: Rejects releases with active unexempted HIGH/CRITICAL CVEs.
- **A4-QLF-004: Release Audit Ledger Integrator** (6.0 EH)
  - *Subsystem*: `platform_core/audit/release_audit.py`
  - *Objective*: Append cryptographic `RELEASE_QUALIFIED` and `RELEASE_MINTED` records to `audit_log.jsonl`.
  - *Dependencies*: Existing `audit_logger.py`.
  - *Acceptance*: Maintains unbroken SHA-256 audit chaining under file locking.

### Milestone 5: Promotion Engine & Two-Person Production Gate (32.0 EH)
- **A4-PRM-001: Zero-Rebuild Promotion Engine** (10.0 EH)
  - *Subsystem*: `platform_core/engine/promotion_engine.py`
  - *Objective*: Dispatch immutable releases across environments without recompilation.
  - *Dependencies*: A4-MAN-002, A4-REG-002.
  - *Acceptance*: Verifies byte-for-byte digest parity in target environment before deployment.
- **A4-PRM-002: Two-Person Production Governance Gate** (10.0 EH)
  - *Subsystem*: `platform_core/policy/two_person_gate.py`
  - *Objective*: Enforce distinct authenticated Requester vs Approver and active `CHG-*` change ticket.
  - *Dependencies*: A4-PRM-001.
  - *Acceptance*: Blocks self-approval; validates change ticket status = `APPROVED`.
- **A4-PRM-003: Release Declarative Jenkinsfile** (8.0 EH)
  - *Subsystem*: `ci-cd/jenkins/pipelines/release/Jenkinsfile.release`
  - *Objective*: Multi-stage release pipeline orchestrating ingestion, qualification, signing, and promotion.
  - *Dependencies*: Existing Jenkins Shared Library.
  - *Acceptance*: Successfully runs in Jenkins; handles promotion parameters and manual input gates.
- **A4-PRM-004: Trusted Shared Library Release Steps** (4.0 EH)
  - *Subsystem*: `ci-cd/jenkins/shared-library/vars/neroRelease.groovy`
  - *Objective*: Reusable Groovy steps for release qualification, signing, and promotion.
  - *Dependencies*: A4-PRM-003.
  - *Acceptance*: Shared library methods pass Jenkins syntax checks and CPS transformation.

### Milestone 6: Rollback Engineering, Retention, Revocation & E2E Suite (28.0 EH)
- **A4-ROL-001: Deterministic Rollback Orchestrator** (8.0 EH)
  - *Subsystem*: `platform_core/engine/rollback_engine.py`
  - *Objective*: Implement 10-step rollback redeploying prior immutable release manifest.
  - *Dependencies*: A4-PRM-001.
  - *Acceptance*: Restores prior release in $<30$ seconds with zero recompilation; verifies health.
- **A4-RET-001: Artifact Lifecycle & Retention Sweeper** (6.0 EH)
  - *Subsystem*: `platform_core/policy/retention_sweeper.py`
  - *Objective*: Enforce environment retention tiers; protect active deployments and rollback dependencies.
  - *Dependencies*: A4-REG-002.
  - *Acceptance*: Purges orphaned historical tags; never deletes active or protected rollback digests.
- **A4-REV-001: Release Revocation Coordinator** (6.0 EH)
  - *Subsystem*: `platform_core/policy/revocation_coordinator.py`
  - *Objective*: Mark unsafe releases as `REVOKED`; block subsequent promotions; preserve forensic blobs.
  - *Dependencies*: A4-QLF-002.
  - *Acceptance*: Immediately halts active promotion; records `RELEASE_REVOKED` in audit ledger.
- **A4-TST-001: End-to-End Release Qualification Suite** (8.0 EH)
  - *Subsystem*: `tests/integration/test_release_engineering.py`
  - *Objective*: Comprehensive automated test suite qualifying all 4 reference applications through release and rollback.
  - *Dependencies*: All previous tasks.
  - *Acceptance*: 100% test pass rate across all reference applications and failure injection cases.

**Total Planned Engineering Hours: 188.0 EH Across 24 Tasks**

---

## 9. Engineering Effort Estimation & Resource Planning

### Three-Point PERT Effort Estimation
Using standard software engineering PERT estimation ($E = \frac{O + 4M + P}{6}$):

| Milestone | Optimistic ($O$) | Most Likely ($M$) | Conservative ($P$) | PERT Expected ($E$) |
|---|:---:|:---:|:---:|:---:|
| **M1: Candidate Ingestion & Manifest v2** | 26.0 EH | 30.0 EH | 38.0 EH | 30.7 EH |
| **M2: Registry Adapters & Distribution** | 28.0 EH | 32.0 EH | 40.0 EH | 32.7 EH |
| **M3: Supply Chain Security (Syft/Cosign)**| 28.0 EH | 34.0 EH | 44.0 EH | 34.7 EH |
| **M4: Qualification Engine & Policy** | 28.0 EH | 32.0 EH | 38.0 EH | 32.3 EH |
| **M5: Promotion Engine & Two-Person Gate** | 28.0 EH | 32.0 EH | 40.0 EH | 32.7 EH |
| **M6: Rollback, Retention & E2E Suite** | 24.0 EH | 28.0 EH | 34.0 EH | 28.3 EH |
| **TOTAL PROGRAMME 1 PHASE A4** | **162.0 EH** | **188.0 EH** | **234.0 EH** | **189.4 EH** |

### Discipline Breakdown of Effort
- **Architecture & System Design**: 24.0 EH (12.8%)
- **Core Software Development**: 86.0 EH (45.7%)
- **Subsystem & Pipeline Integration**: 34.0 EH (18.1%)
- **Test Suite & Failure Injection Engineering**: 24.0 EH (12.8%)
- **Debugging & Edge-Case Remediation**: 10.0 EH (5.3%)
- **Runbooks & Operational Documentation**: 10.0 EH (5.3%)

### Workstation & Infrastructure Resource Allocations
- **CPU**: 4 Cores (Allocated to Docker, Jenkins, and Python pytest).
- **RAM**: 8 GB Working Memory (Jenkins ~1.5 GB, Local Registry ~50 MB, Floci ~200 MB, Test harnesses ~1 GB).
- **Disk Storage**: 15 GB Free Disk Space (Container images, layer caches, and S3 release tarballs).
- **Cloud Expenditure**: **$0.00** (Floci-first local lab execution; zero real cloud charges).

---

## 10. Reference Application Release Qualification Portfolio

The Phase A4 release engineering capability will be qualified against all four reference applications in the central catalog:

```text
===================================================================================================
                       REFERENCE APPLICATION RELEASE QUALIFICATION SCENARIOS
===================================================================================================
  1. hotel-billing (Multi-Component Microservice)
     - Components  : backend (Java 17 container on port 8082), frontend (Node 22 static tarball)
     - Release Flow: Parallel build -> OCI push + S3 tarball push -> CycloneDX SBOM -> Cosign sign
     - Promotion   : Develop -> QA -> Staging -> Production (Two-Person Approval Gate + CHG ticket)
     - Rollback    : Revert backend to prior container digest; revert frontend to prior S3 tarball

  2. sample-node-service (Single-Component API Microservice)
     - Components  : api (Node 22 Express container on port 8080)
     - Release Flow: Hermetic build -> OCI push -> Syft SBOM -> Cosign sign -> Manifest mint
     - Promotion   : Develop -> QA (automated smoke) -> Staging -> Production
     - Rollback    : Atomic rolling update to prior qualified container digest

  3. sample-python-worker (Asynchronous Background Worker)
     - Components  : worker (Python 3.12 FastAPI / SQS consumer)
     - Release Flow: Distroless container build -> OCI push -> SBOM -> Cosign sign
     - Promotion   : Zero-rebuild promotion across all environments
     - Rollback    : Immediate worker task redirection to prior digest

  4. sample-go-service (High-Performance Hexagonal Microservice)
     - Components  : api (Go 1.27.3 static binary on Distroless debian12:nonroot)
     - Release Flow: Hermetic multi-stage build -> OCI push -> SBOM -> Cosign sign
     - Promotion   : Sequential promotion; synthetic health verification on /health
     - Rollback    : Immediate container redeployment to prior qualified digest
===================================================================================================
```

---

## 11. Testable Acceptance Criteria (17 Mandatory Conditions)

Phase A4 implementation will be accepted only when all 17 conditions are empirically validated:
1. **Candidate Contract Ingestion**: Ingests and validates `CandidateReleaseContract` from `ci_evidence.json`.
2. **Invalid Candidate Blockade**: Failed CI runs, test failures, or diff coverage $<80\%$ are strictly rejected.
3. **Multi-Component Manifest Validation**: Manifest v2 validates multi-component apps (`hotel-billing`).
4. **Digest Pining**: Every container image is bound to a verified 64-character SHA-256 digest (`image@sha256:...`).
5. **Artifact Publication**: Images push successfully to `localhost:5100`; tarballs upload to S3.
6. **CycloneDX SBOM Generation**: Valid CycloneDX 1.5 JSON SBOMs are generated and referenced.
7. **In-Toto Provenance**: Hermetic SLSA-compliant build provenance attestations are generated.
8. **Cosign Signature Verification**: Detached signatures are verified offline using `cosign.pub`.
9. **Idempotent Registration**: Re-registering an identical release succeeds idempotently.
10. **Zero-Rebuild Promotion**: Higher environments deploy the exact digest validated in develop without rebuilding.
11. **Two-Person Production Gate**: Production promotion requires distinct Requester and Approver with a valid `CHG-*` ticket.
12. **Deterministic Rollback**: Redeploys prior qualified release in $<30$ seconds with zero recompilation.
13. **Active Deployment Retention Protection**: Active deployments and rollback targets are locked against deletion.
14. **Release Revocation Blockade**: Revoked releases cannot be promoted to any environment.
15. **Cryptographic Audit Chaining**: All release operations append valid SHA-256 chained records to `audit_log.jsonl`.
16. **Terraform Baseline Preservation**: `terraform.tfstate` remains Serial 23 with 15 Managed Resources.
17. **Zero Cloud Expenditure**: All tests pass locally with $0.00 cloud spend.

---

## 12. Programmatic Entry and Exit Gates

### Phase A4 Entry Gate (Prerequisites)
- [x] Phase A3 Closure Verified (`NERO_A3_CLOSURE_VERIFICATION_REPORT.md` approved).
- [x] Candidate CI evidence contract format available (`ci_evidence.json`).
- [x] Local private OCI registry operational on `localhost:5100`.
- [x] Floci S3 operational on `http://localhost:4566`.
- [x] Cryptographic audit ledger operational (82 chained records).
- [x] Platform owner authorization recorded for Phase A4 implementation.

### Phase A4 Exit Gate (Completion Criteria)
- Complete delivery of all 24 Phase A4 engineering tasks.
- 100% pass rate across the automated release engineering qualification suite.
- Operational verification of Zero-Rebuild Promotion and Rollback across all 4 reference applications.
- Cryptographic verification of the expanded audit ledger.
- Terraform state serial 23 preserved.
- Net cloud expenditure verified at \$0.00.

---

## 13. Governance Checklists

In accordance with Programme 1 governance protocol, both checklists remain **unchecked** awaiting explicit platform owner review:

### Gate A — A3 Closure
- [ ] A3 implementation verified across all 24 tasks.
- [ ] SCM integration verified at Level 1 (fixtures) and Level 2 (local signed requests).
- [ ] Universal CI pipeline verified across all 4 reference applications.
- [ ] DevSecOps scanning verified (Gitleaks, Semgrep, Trivy).
- [ ] CI candidate evidence verified (`ci_evidence.json`).
- [ ] Outstanding A3 operational limitations accepted.

### Gate B — A4 Architecture and Scope Approval
- [ ] A4 scope and 24-task Work Breakdown Structure accepted.
- [ ] Universal Immutable Release Manifest v2 architecture accepted.
- [ ] Decoupled artifact repository architecture (OCI Registry + S3) accepted.
- [ ] Software supply chain security approach (Syft SBOM + Cosign) accepted.
- [ ] Zero-rebuild promotion and deterministic rollback design accepted.
- [ ] Retention tiers and release revocation policy accepted.
- [ ] Engineering effort estimate of 188.0 EH accepted.
- [ ] A4 implementation explicitly authorized by platform owner.
