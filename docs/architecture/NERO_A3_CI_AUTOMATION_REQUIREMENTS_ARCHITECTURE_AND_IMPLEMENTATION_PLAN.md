# NERO ENTERPRISE DEVOPS AUTOMATION PLATFORM
# PROGRAMME 1 — PHASE A3
# COMPLETE CONTINUOUS INTEGRATION AUTOMATION
## System Architecture, Detailed Requirements & Implementation Plan

**Document ID:** NERO-A3-PLAN-001  
**Programme:** Universal Enterprise DevOps Automation Platform  
**Track:** Programme 1 — Deterministic DevOps Automation First  
**Milestone:** Phase A3 — Complete Continuous Integration Automation  
**Authoritative Baseline:** `nero_devops_standard/`  
**Deployment Model:** Local Floci Simulation / Enterprise Hybrid  
**Primary Orchestrator:** Jenkins Master & Ephemeral Build Agents  
**Target Execution Environment:** Zero Real Cloud Spend ($0.00) / Air-Gapped Floci  
**Implementation Authorization Status:** **PLANNING ONLY (Not Authorized for Implementation)**  

---

## 1. Executive Summary & Product Objective

The primary objective of **NERO Programme 1, Phase A3** is to build a complete, automated, event-driven Continuous Integration (CI) platform that eliminates manual pipeline triggering, bespoke CI scripts, and unverified code merges.

### 1.1 The Phase A3 Vision
When a developer commits code and pushes to a registered enterprise repository (or opens a pull request):
```
Developer Push / PR
  │
  ▼
[HMAC Webhook Gateway] ──► Validates cryptographic signature & secret
  │
  ▼
[Idempotency Engine]   ──► Deduplicates delivery & checks replay attacks
  │
  ▼
[Catalog Authorization]──► Validates repository URL, branch, & security tier
  │
  ▼
[Universal CI Pipeline]──► Evaluates app.spec.yaml & selects typed adapters
  │
  ├─► [Parallel Builds]     ──► Compiles Java, Node, Python, Go in hermetic containers
  ├─► [Automated Testing]   ──► Executes unit, integration, API, & contract tests
  ├─► [Code Quality Gate]   ──► Checks code smells, complexity, & coverage (>= 80%)
  ├─► [DevSecOps Scanners]  ──► Gitleaks (Secrets) + Semgrep (SAST) + Trivy (CVE)
  ├─► [Supply Chain SBOM]   ──► Syft (CycloneDX 1.5) + Cosign signing
  │
  ▼
[CI Evidence Ledger]   ──► Generates cryptographic ci_evidence.json & audit record
  │
  ▼
[Developer Feedback]   ──► Posts commit/PR status & actionable diagnostics
```

Phase A3 extends the declarative **`app.spec.yaml`** v2 and **Central Application Catalog** foundation qualified in Phase A2 without modifying core catalog abstractions.

---

## 2. Core Architectural Framework

### 2.1 Component Architecture & Topology

```
┌────────────────────────────────────────────────────────────────────────┐
│                   PHASE A3 SYSTEM ARCHITECTURE                         │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│   [Git SCM: GitHub / Bitbucket / GitLab]                               │
│              │                                                         │
│              │ (1) Webhook Event (X-Hub-Signature-256)                 │
│              ▼                                                         │
│   ┌────────────────────────────────────────────────────────┐           │
│   │ SCM Webhook Gateway (`webhook_gateway.py`)             │           │
│   │  - HMAC-SHA256 signature verification                  │           │
│   │  - Replay attack defense (timestamp +/- 300s)          │           │
│   │  - Event payload extraction (ref, commit, PR, sender)  │           │
│   └────────────────────────────────────────────────────────┘           │
│              │                                                         │
│              │ (2) Verified Event                                      │
│              ▼                                                         │
│   ┌────────────────────────────────────────────────────────┐           │
│   │ CI Idempotency Engine (`idempotency_engine.py`)        │           │
│   │  - Nonce & delivery UUID tracking                      │           │
│   │  - Commit SHA deduplication window (10 mins)           │           │
│   │  - Fast rejection of duplicate webhooks                │           │
│   └────────────────────────────────────────────────────────┘           │
│              │                                                         │
│              │ (3) Trigger CI Job via API Token                        │
│              ▼                                                         │
│   ┌────────────────────────────────────────────────────────┐           │
│   │ Jenkins Primary Orchestrator (Universal CI Pipeline)   │           │
│   │  - Stage 1: Preflight Catalog Authorization            │           │
│   │  - Stage 2: Spec Confinement & Lockfile Check          │           │
│   │  - Stage 3: Parallel Component Build Orchestrator      │           │
│   │  - Stage 4: Multi-Layer Automated Test Runner          │           │
│   │  - Stage 5: Code Quality & Coverage Gates              │           │
│   │  - Stage 6: DevSecOps SAST, Secret, & CVE Scans        │           │
│   │  - Stage 7: SBOM Generation & Provenance               │           │
│   │  - Stage 8: Structured CI Evidence Ledger Record       │           │
│   │  - Stage 9: Developer Feedback & PR Status Publisher   │           │
│   └────────────────────────────────────────────────────────┘           │
│              │                                                         │
│              ├────────────────────────┬────────────────────────┐       │
│              ▼                        ▼                        ▼       │
│   [Ephemeral Build Agent]   [Quality Gate]            [Audit Ledger]   │
│    (Isolated Container)     (SonarQube Server)        (audit_log.jsonl)│
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Functional Requirements

### 3.1 SCM Integration & Webhook Security Gateway
- **REQ-A3-SCM-001 (Multi-Provider Support)**: Provide adapter interfaces for GitHub, Bitbucket Server/Cloud, GitLab, and generic self-hosted Git servers.
- **REQ-A3-SCM-002 (Cryptographic Webhook Verification)**: Require HMAC-SHA256 signature validation against a pre-shared secret configured per repository. Unsigned or invalidly signed webhooks must be rejected with HTTP 401/403 and logged.
- **REQ-A3-SCM-003 (Replay Attack Defense)**: Reject payloads with event timestamps older or newer than 300 seconds from local clock.
- **REQ-A3-SCM-004 (Branch Policy Awareness)**: Enforce catalog `allowed_branches` before triggering CI builds. Pushes to unauthorized branches fail closed with zero compute consumed.

### 3.2 Automated CI Trigger & Idempotency Engine
- **REQ-A3-TRG-001 (Supported Events)**:
  - `push`: Direct push to approved branch.
  - `pull_request.opened`: New PR initiated.
  - `pull_request.synchronize`: New commits pushed to existing PR.
  - `pull_request.reopened`: Existing PR reopened.
  - `release.published`: Tagged release branch.
  - `manual`: Authorized manual build trigger via Jenkins parameters.
- **REQ-A3-TRG-002 (Idempotency Engine)**:
  - Every incoming webhook generates a deterministic event key: `hash(repo_url + commit_sha + event_type)`.
  - Maintain a sliding-window cache (stored in `platform_core/ci/event_cache.json`) for 600 seconds.
  - Duplicate deliveries return HTTP 200 `[ALREADY_PROCESSING]` without triggering redundant Jenkins builds.

### 3.3 The 12-Step Pull Request Validation Workflow
Every pull request must pass 12 mandatory quality and security checks before receiving CI qualification status:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   12-STEP PULL REQUEST VALIDATION                      │
├────────────────────────────────────────────────────────────────────────┤
│  1. Catalog Authorization:     Verify repo URL and target branch        │
│  2. Branch Protection:         Verify source/target branch policies     │
│  3. Specification Check:       Validate app.spec.yaml against v2 schema │
│  4. Change Metadata:           Verify commit message and author identity│
│  5. Dependency Lockfile:       Enforce package-lock / pom / go.mod      │
│  6. Automated Unit Tests:      Execute unit suites with JUnit parsing   │
│  7. Automated Integration:     Execute integration suites in Floci      │
│  8. Code Quality Analysis:     Check complexity and code smells         │
│  9. Secret Scanning:           Run Gitleaks on PR commit delta          │
│ 10. Dependency CVE Scan:       Run Trivy SCA on lockfiles               │
│ 11. Security Policy Gate:      Enforce non-root and supported runtimes  │
│ 12. PR Status Reporting:       Publish structured check status to Git   │
└────────────────────────────────────────────────────────────────────────┘
```
*A failure in any mandatory check (1–11) marks the PR as FAILED and blocks qualification.*

### 3.4 Universal Build Orchestration
- **REQ-A3-BLD-001 (Dynamic Selection)**: Pipeline must select build adapters dynamically based on `spec.spec.components[].build.adapter`:
  - `java-maven` / `dockerfile`: Java 17 Spring Boot builds.
  - `node`: Node.js 22 Express APIs and Vite React SPAs.
  - `go`: Go 1.27.3 static compilation targeting Distroless.
  - `python`: Python 3.12 hermetic containers.
- **REQ-A3-BLD-002 (Parallel Component Execution)**: In multi-component applications (e.g. `hotel-billing` with backend container and frontend SPA), independent components must build in parallel within configured resource thresholds.
- **REQ-A3-BLD-003 (Build Caching)**: Cache dependency directories (`~/.m2`, `~/.npm`, `/go/pkg/mod`, `~/.cache/pip`) across builds while invalidating on lockfile modification.

### 3.5 Automated Testing Engine
- **REQ-A3-TST-001 (Test Discovery & Execution)**: Discover test commands declared in `app.spec.yaml` or language standard conventions:
  - Java: `mvn test`
  - Node: `npm test -- --ci`
  - Python: `pytest tests/unit/ --junitxml=junit.xml`
  - Go: `go test -v -cover ./...`
- **REQ-A3-TST-002 (Machine-Readable Collection)**: Standardize all test outputs to JUnit XML. Parse total tests, passes, failures, errors, and skipped counts.
- **REQ-A3-TST-003 (Flakiness & Timeout Management)**: Enforce individual test stage timeouts (max 10 minutes). Log test execution duration to detect regressions and flaky tests.

### 3.6 Code Quality & Static Analysis
- **REQ-A3-QLT-001 (Quality Gate Metrics)**:
  - Code Smells: Max 0 new blocker / critical issues.
  - Cyclomatic Complexity: Max complexity 15 per function/method.
  - Code Duplication: Max 3% duplicated blocks on new code.
- **REQ-A3-QLT-002 (Test Coverage Threshold)**: Enforce minimum **80% line coverage** on new code delta. Fail build if coverage drops below threshold unless an approved exemption exists.

### 3.7 DevSecOps CI Integration
- **REQ-A3-SEC-001 (Secret Scanning)**: Execute Gitleaks on commit diff (`--log-opts="origin/main..HEAD"`). Terminate immediately if unmasked secrets are detected.
- **REQ-A3-SEC-002 (Static Application Security Testing)**: Execute Semgrep OSS rulesets (`p/default`, `p/owasp-top-ten`). Output SARIF report. Fail closed on `ERROR` severity findings.
- **REQ-A3-SEC-003 (Dependency Vulnerability Scanning)**: Execute Trivy in filesystem mode against lockfiles. Fail closed on `CRITICAL` or `HIGH` vulnerabilities with available fixes.
- **REQ-A3-SEC-004 (SBOM & Provenance)**: Generate CycloneDX 1.5 JSON SBOM via Syft for every built artifact. Sign SBOM and release metadata via Cosign.

### 3.8 Jenkins CI Pipeline Architecture
- **REQ-A3-JNK-001 (Dedicated CI Pipeline)**: Create `ci-cd/jenkins/pipelines/ci/Jenkinsfile.ci` optimized for continuous integration (distinct from multi-environment promotion pipeline).
- **REQ-A3-JNK-002 (Agent Isolation)**: Ephemeral containerized agents. Docker daemon access controlled via non-privileged execution or locked socket permissions to prevent host breakout.
- **REQ-A3-JNK-003 (Shared Library Integration)**: Package reusable CI steps into `ci-cd/jenkins/shared-library/vars/neroCI.groovy`.

### 3.9 CI Event & Evidence Model
- **REQ-A3-EVN-001 (Structured CI Record)**: Every pipeline run produces [`ci_evidence.json`](file:///d:/project/billing-system-master/billing-system-master/platform_core/manifests/ci_evidence.json):
  ```json
  {
    "schema_version": "1.0.0",
    "ci_run_id": "ci-hotel-billing-20261108163000-b15",
    "application_id": "hotel-billing",
    "git": {
      "repository": "https://github.com/ameerarsath/billing-system.git",
      "commit_sha": "a1b2c3d4...",
      "branch": "main",
      "pull_request_id": null
    },
    "jenkins": {
      "job": "universal-ci-pipeline",
      "build_number": 15,
      "duration_seconds": 142.5,
      "result": "SUCCESS"
    },
    "test_summary": {
      "total": 116,
      "passed": 116,
      "failed": 0,
      "skipped": 0,
      "coverage_percentage": 84.5
    },
    "security_summary": {
      "secrets_detected": 0,
      "sast_issues": 0,
      "cve_critical": 0,
      "cve_high": 0
    },
    "artifacts": [
      {
        "component": "backend",
        "image": "backend:rel-20261108163000",
        "digest": "sha256:ec245ac1..."
      }
    ],
    "timestamp": "2026-11-08T11:00:00Z"
  }
  ```
- **REQ-A3-EVN-002 (Cryptographic Audit Chaining)**: Append CI run outcome to [`platform_core/audit/audit_log.jsonl`](file:///d:/project/billing-system-master/billing-system-master/platform_core/audit/audit_log.jsonl) with SHA-256 hash chaining.

### 3.10 Developer Feedback & Notifications
- **REQ-A3-FDB-001 (Status Publishing)**: Post GitHub / SCM commit status (Pending, Success, Failure) linked to build logs.
- **REQ-A3-FDB-002 (PR Summary Table)**: Post markdown summary comment to PR detailing test counts, coverage, and security scan status.
- **REQ-A3-FDB-003 (Secret Masking)**: Scrub all logs and PR feedback to guarantee zero credentials or tokens are displayed in public comments.

---

## 4. Threat Modeling & DevSecOps for CI

| Threat ID | Threat Description | Attack Vector | Automated Countermeasure | Verification Test |
| :--- | :--- | :--- | :--- | :--- |
| **THREAT-A3-001** | Webhook Spoofing / Tampering | Attacker posts forged webhook payload to trigger unauthorized pipelines. | HMAC-SHA256 signature verification against secret. Constant-time comparison. | `test_reject_unsigned_webhook` |
| **THREAT-A3-002** | Webhook Replay Attack | Attacker captures valid payload and replays it repeatedly to exhaust CI resources. | Timestamp freshness window (+/- 300s) + Nonce deduplication cache. | `test_reject_replayed_webhook` |
| **THREAT-A3-003** | Malicious Fork PR Execution | PR from external fork executes malicious commands in CI build agent. | Require manual authorization or catalog registration for forks. Isolated non-root agent containers. | `test_block_unauthorized_fork_pr` |
| **THREAT-A3-004** | Secret Exfiltration via PR Logs | Developer prints `AWS_SECRET_ACCESS_KEY` or JWT token in test output. | `SecretScrubber` stream filter active on all console streams; fails build on leak attempt. | `test_secret_scrubber_blocks_leak` |
| **THREAT-A3-005** | Docker Socket Breakout | Malicious build script mounts host root via `/var/run/docker.sock`. | Restrict Docker socket access; prohibit privileged containers; build via hermetic adapters. | `test_prohibit_privileged_agent` |
| **THREAT-A3-006** | Supply Chain Dependency Poisoning | Malicious upstream package published with typosquatted name. | Lockfile verification required; Trivy SCA scanning before compilation; unpinned builds blocked. | `test_reject_unpinned_dependencies` |
| **THREAT-A3-007** | Quality Gate Bypass | Developer modifies pipeline to skip tests or coverage checks. | CI pipeline definition stored in protected Jenkins master repository, not application repo. | `test_pipeline_integrity_immutable` |

---

## 5. Work Breakdown Structure (WBS) & Task Inventory

Phase A3 is organized into **6 engineering milestones** encompassing **24 discrete engineering tasks**:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   PHASE A3 WORK BREAKDOWN STRUCTURE                    │
├────────────────────────────────────────────────────────────────────────┤
│ Milestone 1: SCM Adapter Contracts & Webhook Security Gateway (30 EH)  │
│ Milestone 2: CI Trigger Engine & Pull Request Validator (28 EH)        │
│ Milestone 3: Universal Build Orchestration & Caching (32 EH)           │
│ Milestone 4: Automated Testing & Code Quality Gates (32 EH)            │
│ Milestone 5: DevSecOps Scanners & Supply Chain Security (36 EH)        │
│ Milestone 6: CI Qualification Suite & Developer Runbooks (26 EH)       │
├────────────────────────────────────────────────────────────────────────┤
│ TOTAL ESTIMATED ENGINEERING EFFORT: 184.0 Engineering Hours            │
└────────────────────────────────────────────────────────────────────────┘
```

### Detailed Task Inventory

| Task ID | Task Title | Subsystem / Location | Scope & Implementation Details | Complexity | Risk | Est. Hours |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| **A3-SCM-001** | SCM Provider Adapter Base Contract | `platform_core/adapters/scm/base.py` | Codify `BaseSCMAdapter` with methods `verify_webhook`, `get_commit_metadata`, `publish_status`, `post_comment`. | Medium | Low | 8 EH |
| **A3-SCM-002** | GitHub Webhook Security Adapter | `platform_core/adapters/scm/github_adapter.py` | Implement HMAC-SHA256 signature verification, constant-time compare, event deserialization. | Medium | Med | 8 EH |
| **A3-SCM-003** | Bitbucket & GitLab SCM Adapters | `platform_core/adapters/scm/bitbucket_adapter.py` | Implement Bitbucket token verification and GitLab secret token header checking. | Medium | Low | 6 EH |
| **A3-SCM-004** | Webhook Gateway HTTP Service | `platform_core/ci/webhook_gateway.py` | Lightweight HTTP receiver service listening on port 8200 routing verified events. | Medium | Med | 8 EH |
| **A3-TRG-001** | Event Deduplication & Idempotency Store | `platform_core/ci/idempotency_engine.py` | Sliding-window deduplication store caching event keys for 600s with TTL. | Medium | Low | 8 EH |
| **A3-TRG-002** | 12-Step PR Validation Engine | `platform_core/ci/pr_validator.py` | Orchestrate 12 mandatory PR validation checks; emit structured validation report. | High | Med | 10 EH |
| **A3-TRG-003** | Jenkins Trigger Bridge | `platform_core/ci/jenkins_trigger.py` | Dispatch authenticated build triggers to Jenkins REST API with parameters and crumb. | Medium | Low | 6 EH |
| **A3-TRG-004** | SCM Status & Feedback Publisher | `platform_core/ci/feedback_publisher.py` | Post pending/success/failure statuses and PR summary tables back to SCM. | Low | Low | 4 EH |
| **A3-BLD-001** | Multi-Component Parallel Build Dispatcher | `platform_core/engine/build_orchestrator.py` | Orchestrate concurrent component builds with thread pool and resource throttling. | High | Med | 10 EH |
| **A3-BLD-002** | Build Cache Management Subsystem | `platform_core/engine/cache_manager.py` | Manage hash-based dependency caching for Maven, npm, pip, and Go modules. | Medium | Low | 8 EH |
| **A3-BLD-003** | Universal CI Jenkinsfile | `ci-cd/jenkins/pipelines/ci/Jenkinsfile.ci` | Author dedicated declarative CI pipeline with parallel stages and JUnit publishing. | High | Med | 8 EH |
| **A3-BLD-004** | Trusted Shared Library CI Steps | `ci-cd/jenkins/shared-library/vars/neroCI.groovy` | Codify reusable Groovy steps for lint, test, scan, and evidence capture. | Medium | Low | 6 EH |
| **A3-TST-001** | Test Discovery & Execution Engine | `platform_core/engine/test_orchestrator.py` | Discover tests declared in `app.spec.yaml` or language standard test harnesses. | Medium | Low | 8 EH |
| **A3-TST-002** | JUnit XML Parser & Test Aggregator | `platform_core/engine/junit_aggregator.py` | Parse polyglot JUnit XML reports; aggregate passes, failures, and execution times. | Low | Low | 6 EH |
| **A3-TST-003** | Test Flakiness & Regression Detector | `platform_core/engine/flakiness_detector.py` | Compare test execution history to flag intermittent tests and timing regressions. | Medium | Low | 8 EH |
| **A3-TST-004** | Code Coverage Aggregator & Gate | `platform_core/engine/coverage_gate.py` | Ingest JaCoCo, c8, pytest-cov, and go-cover reports; enforce 80% threshold. | Medium | Med | 10 EH |
| **A3-SEC-001** | Gitleaks Secret Scanning Integration | `platform_core/adapters/security/gitleaks_adapter.py` | Execute Gitleaks CLI against commit delta; fail closed on detected secrets. | Medium | High | 8 EH |
| **A3-SEC-002** | Semgrep SAST Scanning Integration | `platform_core/adapters/security/semgrep_adapter.py` | Execute Semgrep OSS rulesets; export SARIF; fail closed on ERROR findings. | High | Med | 10 EH |
| **A3-SEC-003** | Trivy SCA & Dependency Scanner | `platform_core/adapters/security/trivy_adapter.py` | Scan lockfiles and container images for CVEs; enforce severity thresholds. | High | Med | 10 EH |
| **A3-SEC-004** | Security Exception Management Engine | `platform_core/policy/security_exceptions.py` | Enforce `.nero-security-exceptions.yaml` with justification and 90-day TTL. | Low | Low | 8 EH |
| **A3-EVN-001** | Structured CI Evidence Record Generator | `platform_core/engine/ci_evidence.py` | Compile `ci_evidence.json` aggregating build, test, and security scan outputs. | Medium | Low | 8 EH |
| **A3-EVN-002** | Cryptographic CI Audit Logger Integration | `platform_core/audit/audit_logger.py` | Record `CI_QUALIFICATION` action with SHA-256 chained hash into `audit_log.jsonl`. | Low | Low | 4 EH |
| **A3-EVN-003** | End-to-End CI Qualification Test Suite | `tests/integration/test_ci_pipeline.py` | Comprehensive test suite verifying webhook -> build -> test -> scan -> evidence. | High | Med | 8 EH |
| **A3-EVN-004** | Developer CI Operations Runbook | `docs/runbooks/CI_OPERATIONS_RUNBOOK.md` | Complete developer runbook covering webhook setup, PR checks, and gate triage. | Low | Low | 6 EH |
| **TOTAL** | **24 Engineering Tasks** | **6 Milestones** | **Complete Continuous Integration Automation** | — | — | **184 EH** |

---

## 6. Dependency Graph & Critical Path

```
Milestone 1 (SCM & Webhook Gateway)
  [A3-SCM-001] Base SCM Contract
       │
       ├─────────────────────────────────┐
       ▼                                 ▼
  [A3-SCM-002] GitHub Adapter      [A3-SCM-003] Bitbucket/GitLab
       │                                 │
       └────────────────┬────────────────┘
                        ▼
             [A3-SCM-004] Webhook HTTP Gateway
                        │
                        ▼
Milestone 2 (Trigger Engine & PR Validator)
             [A3-TRG-001] Idempotency Engine
                        │
                        ▼
             [A3-TRG-002] 12-Step PR Validator
                        │
       ┌────────────────┴────────────────┐
       ▼                                 ▼
  [A3-TRG-003] Jenkins Bridge      [A3-TRG-004] Feedback Publisher
       │
       ▼
Milestone 3 (Universal Build Orchestration)
  [A3-BLD-001] Parallel Dispatcher ◄──► [A3-BLD-002] Cache Manager
       │
       ▼
  [A3-BLD-003] Jenkinsfile.ci ◄────────► [A3-BLD-004] Shared Library
       │
       ├─────────────────────────────────┐
       ▼                                 ▼
Milestone 4 (Testing & Quality)    Milestone 5 (DevSecOps CI)
  [A3-TST-001] Test Orchestrator     [A3-SEC-001] Gitleaks Adapter
       │                                 │
       ▼                                 ▼
  [A3-TST-002] JUnit Aggregator      [A3-SEC-002] Semgrep SAST
       │                                 │
       ▼                                 ▼
  [A3-TST-003] Flakiness Engine      [A3-SEC-003] Trivy SCA Scanner
       │                                 │
       ▼                                 ▼
  [A3-TST-004] Coverage Gate         [A3-SEC-004] Exception Engine
       │                                 │
       └────────────────┬────────────────┘
                        ▼
Milestone 6 (Evidence, Qualification & Runbooks)
             [A3-EVN-001] CI Evidence Generator
                        │
                        ▼
             [A3-EVN-002] Audit Ledger Integration
                        │
                        ▼
             [A3-EVN-003] CI Qualification Suite
                        │
                        ▼
             [A3-EVN-004] Operations Runbook
```

---

## 7. Engineering Effort Estimates (Three-Point Estimation)

Following standard PERT estimation methodology:
$$\text{Expected Effort } (E) = \frac{O + 4M + P}{6}$$

Where:
- $O$ = Optimistic estimate (ideal execution, minimal defects)
- $M$ = Most-likely estimate (planned delivery baseline)
- $P$ = Conservative estimate (complex debugging, environment latency)

### 7.1 Milestone-by-Milestone Three-Point Estimates

| Milestone | Optimistic ($O$) | Most Likely ($M$) | Conservative ($P$) | Expected ($E$) | Standard Deviation ($\sigma$) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **M1: SCM Adapter Contracts & Webhook Gateway** | 24 EH | 30 EH | 40 EH | 30.7 EH | 2.67 EH |
| **M2: CI Trigger Engine & PR Validator** | 22 EH | 28 EH | 38 EH | 28.7 EH | 2.67 EH |
| **M3: Universal Build Orchestration & Cache** | 26 EH | 32 EH | 42 EH | 32.7 EH | 2.67 EH |
| **M4: Automated Testing & Code Quality Gates** | 24 EH | 32 EH | 44 EH | 32.7 EH | 3.33 EH |
| **M5: DevSecOps Scanners & Supply Chain** | 28 EH | 36 EH | 50 EH | 37.3 EH | 3.67 EH |
| **M6: Qualification Suite & Runbooks** | 20 EH | 26 EH | 36 EH | 26.7 EH | 2.67 EH |
| **TOTALS** | **144.0 EH** | **184.0 EH** | **250.0 EH** | **188.8 EH** | **7.23 EH** |

### 7.2 Functional Discipline Allocation (Most-Likely: 184 EH)

| Engineering Discipline | Allocated Hours | % of Total | Core Focus |
| :--- | :---: | :---: | :--- |
| **Architecture & Threat Modeling** | 22.0 EH | 12.0% | SCM contract design, webhook threat modeling, token governance |
| **Core Software Development** | 68.0 EH | 37.0% | Webhook gateway, idempotency store, PR validator, scanner adapters |
| **Jenkins Pipeline & Shared Library** | 30.0 EH | 16.3% | `Jenkinsfile.ci`, `neroCI.groovy`, parallel stage coordination |
| **DevSecOps & Tool Integration** | 28.0 EH | 15.2% | Gitleaks, Semgrep, Trivy integration, exception rules engine |
| **Automated Testing & Qualification** | 24.0 EH | 13.0% | JUnit aggregator, coverage gates, full CI integration suite |
| **Technical Documentation & Runbooks** | 12.0 EH | 6.5% | Developer runbooks, troubleshooting guides, architecture specs |
| **TOTAL** | **184.0 EH** | **100.0%** | **Reconciled Discipline Total** |

---

## 8. Local Environment & Hardware Budget

To preserve the **zero cloud cost commitment ($0.00)** and avoid workstation resource exhaustion during parallel builds and security scans, Phase A3 establishes strict local hardware resource limits:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   LOCAL WORKSTATION RESOURCE BUDGET                    │
├────────────────────────────────────────────────────────────────────────┤
│ Total Available System RAM:        32 GB                               │
│ Platform Core & Base Daemons:      6 GB (Floci, Jenkins, Registry)     │
│ SonarQube Server Container:        2.5 GB RAM                          │
│ Parallel CI Build Workers:         Max 2 concurrent workers (3 GB each)│
│ Security Scanners (Trivy/Semgrep): Max 1.5 GB ephemeral burst          │
│ Maximum Simultaneous Memory:       16 GB RAM (Leaves 16 GB for Host OS)│
│ Maximum CPU Concurrency:           4 parallel threads                  │
│ Ephemeral Disk Workspace:          Auto-pruned after every pipeline run│
└────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Phase A3 Acceptance Criteria & Phase A4 Entry Gates

### 9.1 Phase A3 Acceptance Criteria
1. **Webhook Security**: Verified HMAC-SHA256 signature verification rejects forged payloads (HTTP 401/403) and replayed payloads (> 300s).
2. **Idempotent Triggering**: Repeated delivery of identical webhook triggers 0 duplicate pipeline executions.
3. **12-Step PR Validation**: Full 12-check validation executes on pull request simulation; passes clean PRs and blocks violating PRs.
4. **Universal Build Orchestration**: Successfully compiles and packages all 4 reference applications (`hotel-billing`, `sample-node-service`, `sample-python-worker`, `sample-go-service`) using dynamic adapter dispatch.
5. **Testing & Coverage Gates**: Automated JUnit collection verifies passes/failures; blocks builds with < 80% coverage.
6. **DevSecOps Gates**: Gitleaks blocks mock secret commits; Semgrep blocks critical SAST vulnerabilities; Trivy blocks critical CVEs.
7. **Structured CI Evidence**: Every pipeline run outputs valid `ci_evidence.json` cryptographically appended to `audit_log.jsonl`.
8. **100% Test Pass Rate**: Zero regressions on existing 116 tests + 100% pass on new A3 integration suite.
9. **Zero Cloud Expenditure**: Zero real AWS cloud spend ($0.00).
10. **Baseline State Intact**: Local Terraform state remains Serial 23, 15 Managed Resources.

### 9.2 Phase A4 Entry Requirements
Upon successful verification of Phase A3 exit criteria, the platform is eligible to enter:
**Programme 1, Phase A4: Build, Registry & Immutable Release Automation** (Universal container packaging, automated digest pinning, and immutable release manifests).

---

## 10. Formal Owner Approval Gate

```text
================================================================================
 NERO ENTERPRISE DEVOPS AUTOMATION PLATFORM
 GATE 2 / PHASE A3 ARCHITECTURE APPROVAL CHECKLIST
================================================================================

[ ] 1. A2 Closure Verification Report reviewed and accepted (A2_CLOSURE_PARTIALLY_VERIFIED).
[ ] 2. Task inventory reconciliation accepted (22 tasks, 168 EH accounted).
[ ] 3. CI Tool Selection Matrix approved (Gitleaks, Semgrep, Trivy, Syft, Cosign).
[ ] 4. Phase A3 Scope & Architecture Plan approved (24 tasks, 184 EH most-likely).
[ ] 5. Zero-cloud-spend commitment confirmed ($0.00 real cloud spend).
[ ] 6. Workstation resource budget approved (Max 16 GB peak RAM, 4 CPU threads).
[ ] 7. Authorization to begin Phase A3 implementation granted.

Owner Approval Signature: _______________________ Date: ______________
================================================================================
```
