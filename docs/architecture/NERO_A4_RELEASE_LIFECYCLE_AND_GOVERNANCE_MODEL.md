# NERO Universal Enterprise DevOps Automation Platform
# Programme 1 — Phase A4: Release Lifecycle, Governance & Supply Chain Security Model

**Document Type:** Enterprise Governance, Lifecycle & Threat Model Specification  
**Document ID:** NERO-A4-GOV-001  
**Programme:** NERO Programme 1 — Deterministic DevOps Automation First  
**Milestone:** Phase A4 — Immutable Release Engineering & Artifact Repository Integration  
**Status:** **`PROPOSED_AWAITING_OWNER_AUTHORIZATION`**  
**Effective Date:** 2026-11-08  
**Author:** NERO DevSecOps Security Architect & Release Engineering Lead  

---

## 1. Executive Summary & Governance Principles

Phase A4 introduces enterprise-grade governance to the NERO DevOps Automation Platform. In earlier phases, Continuous Integration validated code correctness, tests, and code quality. Phase A4 establishes the formal lifecycle governing how qualified build artifacts transition into **Trusted, Immutable, Deployable Software Releases**.

This governance model is anchored on four foundational architecture principles:
1. **Zero-Rebuild Promotion (ADR-003)**: Software is built and packaged once in development. Higher environments (`qa`, `staging`, `prod`) deploy the exact same immutable artifact digests. Rebuilding, recompiling, or repackaging code in higher environments is strictly forbidden.
2. **Two-Person Production Rule (ADR-005)**: No software release may reach production without explicit, cryptographic sign-off by two distinct authenticated principals (Developer Requester and Independent Release Approver).
3. **Cryptographic Provenance & Attestation**: Every release must carry an unbroken evidence chain linking the source Git commit, CI build parameters, CycloneDX SBOM, in-toto provenance attestation, and Cosign digital signature.
4. **Deterministic Rollback Safety**: Rolling back an application is implemented as the redeployment of a previously qualified immutable release manifest, preserving database schema compatibility via the Expand/Contract pattern.

---

## 2. Immutable Environment Promotion Lifecycle

The NERO environment promotion workflow transitions qualified releases sequentially through four discrete stages:

```text
+---------------------------------------------------------------------------------------------------+
|                              IMMUTABLE PROMOTION LIFECYCLE                                        |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|    +-------------------+       +-------------------+       +-------------------+                  |
|    |      DEVELOP      | ----> |        QA         | ----> |      STAGING      |                  |
|    +-------------------+       +-------------------+       +-------------------+                  |
|    - Initial Build &           - Automated Smoke           - Full Rehearsal                       |
|      Digest Pinning              Verification              - Non-Functional &                     |
|    - CycloneDX SBOM            - Component Digest            Performance Tests                    |
|    - Cosign Digital              Verification              - Data Migration                       |
|      Signature                 - Single-Engineer             Dry-Run                              |
|    - Initial CI Evidence         Clearance                 - Zero-Rebuild Deploy                  |
|                                                                      |                            |
|                                                                      v                            |
|                                                            +-------------------+                  |
|                                                            |    PRODUCTION     |                  |
|                                                            +-------------------+                  |
|                                                            - Two-Person Rule                      |
|                                                            - Change Ticket CHG-*                  |
|                                                            - Verified Signatures                  |
|                                                            - Synthetic Probes                     |
|                                                            - Immutable Audit Log                  |
+---------------------------------------------------------------------------------------------------+
```

### Promotion Protocol & State Validation
At each environment transition, the Promotion Engine executes the following deterministic verification protocol:
1. **Manifest Integrity Check**: Ingests the release manifest (`release-manifest.json`) and calculates its SHA-256 payload checksum against the registered release catalog entry.
2. **Component Digest Verification**: For every component defined in the manifest:
   - For container images: Queries the registry at `localhost:5100` (or AWS ECR) to confirm that the image exists at the pinned 64-character digest (`image@sha256:...`).
   - For static frontends: Verifies that the tarball checksum matches the registered SHA-256 hash.
3. **Digital Signature Assertion**: Verifies the Cosign signature of all container digests against the platform's trusted public key (`cosign.pub`).
4. **Environment Policy Evaluation**: Confirms that the target environment allows the release's security tier and application classification.
5. **Approval Validation**:
   - `develop` $\rightarrow$ `qa`: Automated upon passing all CI and qualification checks.
   - `qa` $\rightarrow$ `staging`: Single engineer clearance with automated integration test pass.
   - `staging` $\rightarrow$ `prod`: Mandatory Two-Person Governance Gate (Section 3).
6. **Promotion Ledger Recording**: Appends a `PROMOTION` event to `audit_log.jsonl` recording source environment, target environment, approvers, and artifact digests.

---

## 3. Two-Person Production Governance Architecture

In strict compliance with **ADR-005**, production deployments require dual-custody authorization:

```text
+---------------------------------------------------------------------------------------------------+
|                           TWO-PERSON PRODUCTION GOVERNANCE WORKFLOW                               |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|  [Step 1] Developer Requests Production Promotion                                                 |
|           - Submits Release ID (e.g. rel-20261108120000)                                         |
|           - Provides valid Change Management Ticket (e.g. CHG-94821)                              |
|           - Identity cryptographically verified via Jenkins authenticated session                 |
|                                     |                                                             |
|                                     v                                                             |
|  [Step 2] Automated Gate Validation                                                               |
|           - Validates CHG-* ticket format, status = APPROVED, and active maintenance window       |
|           - Asserts Release Status == QUALIFIED (passed all 12 qualification checks)              |
|           - Asserts Zero Blocker Vulnerabilities (Gitleaks, Semgrep, Trivy)                       |
|           - Asserts Changed-Code Diff Coverage >= 80.0%                                           |
|                                     |                                                             |
|                                     v                                                             |
|  [Step 3] Independent Senior Approver Review                                                      |
|           - Approver must hold role ROLE_RELEASE_APPROVER or ROLE_SRE_LEAD                        |
|           - Approver ID != Requester ID (Strict Segregation of Duties)                            |
|           - Approver reviews diff, synthetic test results, and rollback plan                      |
|           - Approver signs off via interactive Jenkins input step with token auth                 |
|                                     |                                                             |
|                                     v                                                             |
|  [Step 4] Cryptographic Audit Append & Dispatch                                                   |
|           - Appends TWO_PERSON_APPROVAL record to audit_log.jsonl with chained SHA-256            |
|           - Dispatches zero-rebuild production deployment                                         |
+---------------------------------------------------------------------------------------------------+
```

### Identity and Authentication Rules
- **No Arbitrary Username Strings**: Plain text user strings in web forms are strictly rejected as identity proof. User identity must be derived directly from the authenticated Jenkins user session (`currentBuild.rawBuild.getCause(Cause.UserIdCause)`), authenticated OAuth token, or cryptographically signed request header.
- **Identity Inequality Enforcement**:
  ```python
  if requester_principal.user_id == approver_principal.user_id:
      raise GovernanceViolationError(
          f"Segregation of Duties breach: Requester '{requester_principal.user_id}' "
          f"cannot approve their own production release."
      )
  ```
- **Change Management Integration**: The change ticket `CHG-*` must match an active, approved ticket record. In local lab / Floci mode, tickets are validated against an internal mock change ledger or local change repository.

---

## 4. Rollback Engineering & Disaster Recovery

Rollback in NERO is designed as the **deterministic redeployment of a previously qualified immutable release**. It does not compile rollback patches or mutate git history in production.

```text
+---------------------------------------------------------------------------------------------------+
|                             10-STEP DETERMINISTIC ROLLBACK PROTOCOL                               |
+---------------------------------------------------------------------------------------------------+
|  [Step 1]  Release Identification  : Select prior qualified release manifest (rel-PREVIOUS)       |
|  [Step 2]  Manifest Verification   : Validate manifest structure, checksum, and catalog entry     |
|  [Step 3]  Digest Verification     : Assert all container digests exist in OCI registry           |
|  [Step 4]  Signature Validation    : Verify Cosign signatures for all prior artifact digests      |
|  [Step 5]  Target Compatibility    : Confirm environment infrastructure meets manifest spec       |
|  [Step 6]  Database Compatibility  : Verify schema backward-compatibility (Expand/Contract)      |
|  [Step 7]  Rollback Authorization  : Authenticate on-call SRE lead or incident manager           |
|  [Step 8]  Redeploy Artifacts      : Dispatch verified digests without rebuilding (Zero Rebuild)  |
|  [Step 9]  Health Verification     : Execute 7 synthetic health probes across all services        |
|  [Step 10] Audit Recording         : Append ROLLBACK record with incident ID to audit_log.jsonl   |
+---------------------------------------------------------------------------------------------------+
```

### Component-Specific Rollback Handling
1. **Container Workloads (`backend`, `api`, `worker`)**:
   - Redeploys the prior container task definition pointing to `image@sha256:<prior-digest>`.
   - Utilizes rolling updates with connection draining to avoid dropping in-flight HTTP requests.
2. **Static Web Frontends (`frontend`)**:
   - Pulls the prior static bundle tarball from S3 release storage.
   - Unpacks to the target S3 website bucket.
   - Issues cache invalidation requests for CDN / edge routers.
3. **Database Schema Backward-Compatibility (Expand/Contract Pattern)**:
   - Database migrations must adhere to the **Expand/Contract Rule**:
     - *Phase 1 (Expand)*: Add new nullable columns or tables. Code v1 and v2 both operate cleanly.
     - *Phase 2 (Migrate)*: Backfill data.
     - *Phase 3 (Contract)*: Remove old columns *only in subsequent releases* after v2 has stabilized.
   - Destructive schema drops are strictly forbidden in standard releases, ensuring that reverting application code to v1 never breaks against the active database schema.

---

## 5. Release Repository Governance, Retention & Revocation

### Retention Policy Architecture
Artifact retention prevents disk and registry exhaustion while strictly guaranteeing that active deployments and rollback targets are never purged:

| Environment Tier | Retention Rule | Minimum Keep Count | Maximum Age | Protection Rules |
|---|---|:---:|:---:|---|
| **Development** | Count & Age Based | 10 releases | 14 days | Purges unpromoted builds after 14 days |
| **QA** | Count & Age Based | 5 releases | 30 days | Retains active QA candidate builds |
| **Staging** | Count & Age Based | 5 releases | 60 days | Retains current staging and prior rehearsal |
| **Production** | Indefinite / Legal Hold | All releases | Minimum 365 days | **Protected**: Never purges active release or last 3 prior releases |

### Absolute Deletion Invariants
The Retention Engine enforces two immutable safety checks before allowing any artifact deletion:
1. **Active Deployment Protection**: An artifact referenced by any active container service (`ecs_service`) or active S3 bucket cannot be deleted under any circumstances.
2. **Rollback Dependency Protection**: The release immediately preceding the active production release is designated as an **Immutable Rollback Target** and is locked against cleanup.

### Release Revocation Protocol
If a security vulnerability or critical defect is discovered in a previously released artifact, the platform executes a formal **Release Revocation**:

```text
+---------------------------------------------------------------------------------------------------+
|                                  RELEASE REVOCATION WORKFLOW                                      |
+---------------------------------------------------------------------------------------------------+
|  1. Revocation Request   : Security lead or SRE submits revocation request with CVE / defect ID   |
|  2. Impact Assessment    : Registry inspected to identify all environments running the release    |
|  3. Manifest Update      : Release manifest status updated to REVOKED with revocation reason      |
|  4. Promotion Blockade   : Promotion Engine locks the release; all subsequent promotions aborted   |
|  5. Audit Log Chaining   : Cryptographic RELEASE_REVOKED record appended to audit_log.jsonl       |
|  6. Forensic Preservation: Artifact blobs are preserved (not erased) to support forensic triage  |
+---------------------------------------------------------------------------------------------------+
```

---

## 6. STRIDE Security Threat Assessment

To ensure software supply-chain integrity, Phase A4 conducts an exhaustive **STRIDE Threat Modeling Analysis** across 14 release engineering threat vectors:

| Threat ID | STRIDE Category | Asset Under Attack | Attack Vector | Impact | Likelihood | Mitigation Strategy | Verification Method | Residual Risk |
|---|---|---|---|---|:---:|---|---|:---:|
| **THR-001** | Spoofing | SCM Webhook Delivery | Attacker sends fake commit/PR webhooks to gateway | High | Medium | HMAC-SHA256 verification using secret key in constant time | Unit & integration tests in `test_webhook_gateway.py` | Low |
| **THR-002** | Tampering | Container Image Layers | Attacker modifies image bytes in transit or in registry | Critical | Low | Content-addressable SHA-256 layer digests; Cosign digital signing | `cosign verify` and digest comparison | Minimal |
| **THR-003** | Tampering | Mutable Image Tags | Attacker pushes malicious code to existing tag `api:1.0.0` | Critical | Medium | Client-side tag immutability check; deploy strictly by immutable digest | `test_oci_registry_adapter.py` immutability assertion | Low |
| **THR-004** | Information Disclosure | Registry Credentials | Developer credentials or registry tokens leaked in logs | High | Medium | `SecretScrubber` redaction; Docker auth tokens stored in protected volume | Regex scrub testing; audit log inspection | Low |
| **THR-005** | Spoofing / Tampering | Signing Key Theft | Attacker steals local Cosign private key to sign malware | Critical | Low | Encrypted private key at rest; passphrase managed by `SecretManager` | Passphrase challenge in `CosignAdapter` | Low |
| **THR-006** | Tampering | Release Manifest | Attacker alters image digest inside `release-manifest.json` | Critical | Low | Manifest payload SHA-256 hash verified against catalog & audit ledger | Manifest validation in `release_manager.py` | Minimal |
| **THR-007** | Repudiation / Tampering | Build Provenance | Attacker alters in-toto build provenance attestation | High | Low | In-toto attestation signed alongside container image via Cosign | Cosign attestation verification | Low |
| **THR-008** | Tampering | CycloneDX SBOM | Attacker removes vulnerable libraries from SBOM JSON | High | Low | SBOM generated hermetically in pipeline; signed as OCI artifact | SBOM hash matching in candidate contract | Low |
| **THR-009** | Elevation of Privilege | Release Publication | Unauthorized user attempts to publish a release | Critical | Medium | Jenkins pipeline authentication; catalog authorization preflight | `pr_validator.py` step 1 catalog check | Low |
| **THR-010** | Elevation of Privilege | Production Promotion | Developer self-approves production deployment | Critical | Medium | Two-Person rule: Requester principal != Approver principal | `test_governance_rules.py` dual-custody check | Minimal |
| **THR-011** | Repudiation | Rollback Deployment | Rogue operator deploys obsolete vulnerable release | High | Low | Rollback manifest must be in `QUALIFIED` state; status `REVOKED` blocked | Rollback engine state check | Low |
| **THR-012** | Denial of Service | Registry Deletion | Accidental deletion of active deployment images | High | Low | Active deployment and rollback reference locking before deletion | Retention engine dependency checks | Low |
| **THR-013** | Elevation of Privilege | CI-Release Boundary | Unqualified CI candidate ingested into production | Critical | Low | Candidate contract requires 12 qualification checks, 80% coverage, 0 CVEs | `ReleaseQualificationEngine` 12-step audit | Minimal |
| **THR-014** | Tampering | Cryptographic Audit Log | Operator truncates or mutates `audit_log.jsonl` | Critical | Low | SHA-256 hash chaining (`prev_hash` to `record_hash`); advisory file locking | `verify_audit_ledger` integrity check | Minimal |

---

## 7. Reliability, Resilience & Recovery Requirements

1. **Idempotent Artifact Publication**: Publishing an already published image tag with identical bytes must succeed idempotently without error and return the verified digest.
2. **Atomic Release Registration**: Writing the release manifest to S3, registry, and catalog must be atomic. If any write fails, the entire release registration transaction is rolled back and marked `FAILED`.
3. **Safe Retry Strategy**: Network calls to registries or storage utilize exponential backoff (initial delay 500ms, max 3 retries, jitter 100ms) to withstand transient TCP drops.
4. **Registry Outage Resilience**: If the private registry is temporarily unreachable, running workloads continue operating uninterrupted; new release pipelines fail closed safely.
5. **Partial Multi-Component Failure Protection**: If one component in a multi-component build fails, the entire release is aborted. Incomplete release manifests are never created.
