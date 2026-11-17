# NERO ENTERPRISE DEVOPS AUTOMATION PLATFORM
# PROGRAMME 1 — PHASE A3: CONTINUOUS INTEGRATION AUTOMATION
## CI Tool Compatibility, Evaluation & Selection Matrix

---

## 1. Executive Summary & Evaluation Criteria

Under **Programme 1 (Deterministic DevOps Automation First)**, Phase A3 establishes an automated, event-driven Continuous Integration engine. Every code commit and pull request must undergo automated build orchestration, multi-layer testing, code-quality validation, and DevSecOps security scanning before qualification.

### 1.1 Strict Platform Evaluation Criteria
To maintain compatibility with the **Floci-First hybrid architecture**, zero-cost constraints, and local workstation hardware limits, every candidate CI tool is evaluated against six non-negotiable criteria:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   NERO CI TOOL EVALUATION CRITERIA                     │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Offline / Air-Gapped Execution: Zero mandatory outbound SaaS calls │
│ 2. Permissive Open-Source License: Apache 2.0, MIT, BSD, or LGPL       │
│ 3. Polyglot Coverage: Java 17, Node.js 22, Python 3.12, Go 1.27.3     │
│ 4. Deterministic Machine Output: JSON, SARIF, or JUnit XML formats     │
│ 5. Resource Efficiency: Operates cleanly within workstation memory     │
│ 6. Jenkins Pipeline Portability: Zero proprietary agent dependencies   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Category-by-Category Comprehensive Evaluation

### 2.1 Static Application Security Testing (SAST)

| Tool | License | Multi-Language Support | Offline Mode | Machine Output | Resource Overhead | Verdict & Architecture Decision |
| :--- | :--- | :--- | :---: | :--- | :---: | :--- |
| **Semgrep OSS** | LGPL-2.1 | **Java, Node, Python, Go** (100% stack match) | **YES** (local rule packs) | SARIF, JSON | **Low** (~250MB RAM) | **SELECTED (Primary SAST Engine)**: Universal rules engine, fast local AST scanning, native SARIF export for Jenkins. |
| **SonarQube Community** | LGPL-3.0 | Java, JS/TS, Python, Go | YES (Server required) | Web API, SQ Gate | **High** (~2.5GB RAM server) | **SELECTED (Central Quality Gate)**: Central dashboard, maintains cross-build quality metrics and coverage aggregation. |
| **Bandit** | Apache 2.0 | Python only | YES | JSON | Minimal (~50MB) | **RESERVED**: Targeted Python fallback. |
| **Gosec** | Apache 2.0 | Go only | YES | JSON, SARIF | Minimal (~60MB) | **RESERVED**: Targeted Go security linter. |
| **SpotBugs** | LGPL-2.1 | Java only (bytecode) | YES | XML | Medium (~400MB) | **RESERVED**: Deep Java bytecode analyzer. |

---

### 2.2 Secret Scanning & Leak Prevention

| Tool | License | Scanning Speed | Detection Method | Offline / Local | Git Hook / CI Mode | Verdict & Decision |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **Gitleaks** | MIT | **Ultra-Fast (Go binary)** | Regex + Shannon Entropy | **YES** | **YES (Native CI mode)** | **SELECTED (Primary Secret Scanner)**: Zero dependencies, blazingly fast commit scanning, deterministic SARIF/JSON output. |
| **TruffleHog v3** | AGPL-3.0 | Fast | Regex + Active Verification | Partial (wants to verify) | YES | **REJECTED**: AGPL licensing restrictions and active verification attempts violate offline Floci isolation. |
| **GitGuardian CLI (ggshield)** | Commercial/Freemium | Fast | API-driven heuristics | NO (Requires SaaS key) | YES | **REJECTED**: Violates zero-cost and air-gapped offline requirements. |

---

### 2.3 Software Composition Analysis (SCA) & Vulnerability Scanning

| Tool | License | Ecosystems Covered | Vulnerability DB Update | Local DB Cache | Scan Targets | Verdict & Decision |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| **Trivy** (Aqua) | Apache 2.0 | **Java, npm, pip, go.mod, OS packages** | Downloadable DB (`trivy db`) | **YES** (`~/.cache/trivy`) | Lockfiles, Filesystem, OCI Images | **SELECTED (Primary SCA & CVE Scanner)**: Single tool for dependencies, container images, and misconfigurations. |
| **Grype** (Anchore) | Apache 2.0 | Polyglot + CycloneDX | Daily DB pull | YES | SBOM, Filesystem, Images | **APPROVED ALTERNATIVE**: Pairs with Syft; fast local execution. |
| **OWASP Dependency-Check** | Apache 2.0 | Primarily Java / .NET | Heavy NVD feed download | Slow / Fragile | Maven / Gradle builds | **REJECTED for General CI**: NVD rate limiting and heavy XML downloads cause frequent build timeouts. |
| **npm audit / pip-audit / govulncheck** | Varied | Single-language | Online package registries | Partial | Package manifests | **RESERVED**: Fallback linters per build adapter. |

---

### 2.4 Software Bill of Materials (SBOM) & Supply Chain Security

| Tool | License | Formats Supported | Integration Point | Cryptographic Signing | Verdict & Decision |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **Syft** (Anchore) | Apache 2.0 | **CycloneDX 1.5 JSON**, SPDX 2.3 | Direct CLI & container | N/A (Generator) | **SELECTED (Primary SBOM Generator)**: Deep polyglot package extraction, standardized CycloneDX JSON format. |
| **Cosign** (Sigstore) | Apache 2.0 | OCI Signatures, In-toto Attestations | Keypair or Keyless | **YES (ECDSA / Ed25519)** | **SELECTED (Primary Artifact Signer)**: Signs container images and release manifests locally without cloud KMS. |

---

### 2.5 Dockerfile & Container Linting

| Tool | License | Rules Enforced | Non-Root Checks | Performance | Verdict & Decision |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **Hadolint** | GPL-3.0 | Dockerfile best practices & ShellCheck | **YES (DL3002)** | High (Haskell binary) | **SELECTED**: Prevents Dockerfile security anti-patterns before container build. |
| **Dockle** | Apache 2.0 | CIS Docker Benchmark | **YES** | High | **APPROVED**: Container image compliance auditor. |

---

### 2.6 Code Quality, Static Analysis & Test Coverage

| Tool | Focus Area | Technology | Output Formats | Quality Gate Capability | Verdict & Decision |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **SonarQube Community** | Code Smells, Bugs, Coverage, Duplications | Server (Docker) | Web API, Badges | **Strict (Configurable)** | **APPROVED**: Recommended central quality aggregator. |
| **JaCoCo** | Java Code Coverage | Maven Plugin | XML, HTML, CSV | Build Failure Threshold | **SELECTED**: Standard Java coverage. |
| **c8 / Istanbul** | Node.js / React Coverage | npm CLI | LCOV, text-summary | Threshold Enforcement | **SELECTED**: Standard Node coverage. |
| **pytest-cov** | Python Code Coverage | Pytest plugin | XML, Terminal | `--cov-fail-under` | **SELECTED**: Standard Python coverage. |
| **go test -cover** | Go Code Coverage | Built-in Go tool | Coverprofile, text | Threshold via CLI | **SELECTED**: Native Go coverage. |

---

## 3. Approved Phase A3 Tier-1 Toolset Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                   APPROVED PHASE A3 TIER-1 TOOLSET                     │
├────────────────────────────────────────────────────────────────────────┤
│ • Secret Scanning:       Gitleaks v8.x (Pre-build & PR commit scan)    │
│ • Static Analysis (SAST): Semgrep OSS Community (Multi-language SARIF) │
│ • Dependency CVE (SCA):  Trivy v0.50+ (Filesystem & lockfile mode)     │
│ • Container Scanning:    Trivy Image Scan & Hadolint                   │
│ • SBOM Generation:       Syft v1.x (CycloneDX 1.5 JSON)                │
│ • Supply Chain Signing:  Cosign v2.x (Local Keypair Signing)           │
│ • Test Orchestration:    Universal JUnit XML Collection                │
│ • Central Quality Gate:  SonarQube Community Build (Dockerized)        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Vulnerability Threshold & Exception Governance Policy

### 4.1 Automated Gate Enforcement Matrix

| Gate / Analyzer | Fail-Closed Threshold (Blocks PR & Promotion) | Warning Threshold (Advisory) |
| :--- | :--- | :--- |
| **Secret Scanning (Gitleaks)** | **>= 1 Unmasked Secret or Private Key** | None (Zero tolerance) |
| **SAST (Semgrep)** | **>= 1 ERROR / Critical Security Rule Breach** | WARNING rules logged |
| **Dependency CVE (Trivy)** | **>= 1 CRITICAL or HIGH Severity CVE** | MEDIUM / LOW logged |
| **Container Image (Trivy)** | **>= 1 CRITICAL CVE with Available Fix** | Unfixed CVEs logged |
| **Code Coverage (Polyglot)**| **< 80% Line Coverage on New Code** | < 85% Total Coverage |
| **Automated Tests** | **>= 1 Test Failure in Unit/Integration Suite** | Flaky tests flagged |

### 4.2 Security Exception & Expiration Protocol
When a business-critical deployment must proceed despite an unfixed upstream CVE or false positive, the platform enforces a formal exception protocol:
- Exceptions must be declared in `.nero-security-exceptions.yaml`.
- Requires CVE ID, affected package, justification, approving SecOps lead, and **strict expiration date (maximum 90 days)**.
- Expired exceptions fail closed automatically during preflight scanning.
