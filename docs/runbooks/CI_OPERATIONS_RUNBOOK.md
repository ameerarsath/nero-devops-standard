# NERO Enterprise DevOps Automation Platform
# Continuous Integration (CI) Developer Operations Runbook

**Document ID:** NERO-DOC-CI-001  
**Programme:** NERO Programme 1 — Deterministic DevOps Automation First  
**Phase:** Phase A3 (Complete Continuous Integration Automation)  
**Effective Date:** 2026-11-08  
**Audience:** Application Developers, DevOps Engineers, SREs, Security Approvers  

---

## 1. Overview & Developer Lifecycle

Under NERO Phase A3, Continuous Integration is **strictly event-driven, automated, and deterministic**. Developers do not manually trigger Jenkins jobs for routine code pushes or pull requests. 

When you push code or open a pull request:
1. SCM Provider sends an authenticated webhook to NERO Webhook Gateway (`localhost:8200`).
2. NERO verifies HMAC-SHA256 signatures in constant time.
3. The Idempotency Engine deduplicates the delivery and protects against replay attacks.
4. The 12-Step PR Validation Engine verifies application authorization, branch policies, and dependencies.
5. Jenkins executes the Universal CI Pipeline (`Jenkinsfile.ci`), orchestrating parallel builds, tests, diff-coverage gates, and DevSecOps scans.
6. Structured `ci_evidence.json` is generated, cryptographically signed, and chained to the audit ledger.
7. Status checks and a summary table are published back to your Pull Request.

---

## 2. Configuring Repository Webhooks

### 2.1 GitHub Webhook Configuration
- **Payload URL**: `http://<nero-gateway-host>:8200/webhook/github` (or `/webhook`)
- **Content type**: `application/json`
- **Secret**: Enter your repository pre-shared webhook secret (configured in `platform_config.yaml`).
- **Events**:
  - `Pushes` (commits to branches)
  - `Pull requests` (opened, synchronize, reopened)
- **SSL verification**: Enabled for production domains; disabled only in isolated local lab environments.

### 2.2 Bitbucket Configuration
- **URL**: `http://<nero-gateway-host>:8200/webhook/bitbucket`
- **Triggers**: Repository Push, Pull Request Created, Pull Request Updated.
- **Secret Header**: Configured via Bearer token or HMAC header.

### 2.3 GitLab Configuration
- **URL**: `http://<nero-gateway-host>:8200/webhook/gitlab`
- **Secret token**: `X-Gitlab-Token` matching configured secret.
- **Trigger**: Push events, Merge request events.

---

## 3. The 12-Step Pull Request Validation Workflow

Every pull request must satisfy all 12 checks before receiving a `SUCCESS` status:

| Step # | Check Name | Verification Scope | How to Resolve Failure |
|---|---|---|---|
| **1** | **Catalog Authorization** | Repository URL must match a registered application in `applications.yaml`. | Ensure your repo is onboarded into `platform_core/catalog/applications.yaml`. |
| **2** | **Branch Protection** | Target branch must be in `allowed_branches` (`main`, `develop`, `release/*`). | Target PR to approved integration branches. |
| **3** | **Specification Check** | `app.spec.yaml` must validate against JSON Schema Draft 2020-12 and Pydantic v2. | Run `python -m platform_core.engine.cli inspect-spec app.spec.yaml`. |
| **4** | **Change Metadata** | Valid commit SHA (>= 7 chars) and recognized author email. | Verify local git config (`user.name`, `user.email`). |
| **5** | **Dependency Lockfile** | Enforces pinned dependencies (`pom.xml`, `package-lock.json`, `go.mod`, `requirements.txt`). | Commit your package manager lockfile. Never commit unpinned dependencies. |
| **6** | **Automated Unit Tests** | Automated unit test suites discovered and passing. | Run local unit tests before opening PR. |
| **7** | **Integration Tests** | Mocks and test harnesses configured for local Floci simulation. | Verify integration test configs. |
| **8** | **Code Quality Analysis** | Cyclomatic complexity <= 15 per function, 0 critical code smells. | Refactor overly complex methods. |
| **9** | **Secret Scanning** | Gitleaks scans commit diff for exposed tokens, private keys, or passwords. | Scrub exposed secrets immediately; revoke leaked keys. |
| **10** | **Dependency CVE Scan** | Trivy scans lockfiles for CRITICAL or HIGH vulnerabilities with available fixes. | Bump vulnerable packages to safe versions. |
| **11** | **Security Policy Gate** | Enforces approved runtimes (Java 17, Node 22, Python 3.12, Go 1.23) and non-root containers. | Comply with enterprise runtime policies. |
| **12** | **PR Status Reporting** | Aggregates all steps and publishes markdown feedback table to PR. | Review the generated PR markdown table for detailed failure triage. |

---

## 4. Code Coverage: 80% Changed-Code Diff Gate

NERO enforces a **changed-code diff coverage gate**:
- **Requirement**: At least **80.0%** of lines added or modified in the Pull Request diff must be exercised by unit tests.
- **Baseline Floor Protection**: Total repository coverage cannot drop below the established floor in `coverage_baseline.json`. Legacy code does not need to jump to 80% total coverage immediately, but all new code must meet the standard.
- **Supported Formats**:
  - Java: JaCoCo XML (`target/site/jacoco/jacoco.xml`)
  - Node.js: c8 / LCOV (`coverage/lcov.info`)
  - Python: pytest-cov Cobertura (`coverage.xml`)
  - Go: `coverage.out`

---

## 5. Security Exceptions Policy & Workflow

If a third-party dependency has an open CVE with no upstream patch available, or an integration harness requires a test fixture token:

1. Create an entry in `.nero-security-exceptions.yaml`:
   ```yaml
   exceptions:
     - id: "EXC-2026-042"
       finding_id: "CVE-2023-XXXXX"
       target: "backend/pom.xml"
       justification: "Vulnerability cannot be exploited in air-gapped Floci environment; vendor patch scheduled for Q1"
       approver: "security-lead@enterprise.com"
       created_at: "2026-11-08T00:00:00Z"
       expires_at: "2026-12-08T00:00:00Z" # Maximum 90 days TTL
       revoked: false
   ```
2. **Rules for Approval**:
   - `justification`: Minimum 15 characters, technical business rationale required.
   - `approver`: Named enterprise security engineer.
   - `expires_at`: Mandatory expiration date (max 90 days). Expired exceptions fail closed automatically.
   - Permanent suppressions are strictly prohibited.

---

## 6. Understanding CI Evidence (`ci_evidence.json`)

Every successful CI execution writes a cryptographically validated `ci_evidence.json`:
- Contains Git commit SHA, build number, test statistics, and coverage.
- Lists all built container images with immutable SHA-256 digests.
- Includes a SHA-256 payload checksum.
- Appended to `platform_core/audit/audit_log.jsonl` with hash chaining for non-repudiation.
- Release pipelines (Phase A4) require valid `ci_evidence.json` before promoting artifacts to production.

---

## 7. Troubleshooting & Operational FAQs

### Q1: Webhook returned HTTP 401 Unauthorized
- **Cause**: HMAC-SHA256 signature mismatch or invalid secret.
- **Fix**: Verify the secret in your SCM provider settings matches `NERO_WEBHOOK_SECRET_<PROVIDER>`.

### Q2: Webhook returned HTTP 413 Payload Too Large
- **Cause**: Webhook payload exceeded 1 MB limit.
- **Fix**: Check if large binary files or bloated commit messages were included in the push.

### Q3: Build was marked `[ALREADY_PROCESSING]` or `[ALREADY_COMPLETED]`
- **Cause**: SCM provider resent a duplicate webhook delivery ID within the 600-second window.
- **Fix**: This is normal idempotent deduplication. NERO prevents redundant builds. If you need a re-run, push an empty commit (`git commit --allow-empty`) or trigger manual build via Jenkins parameters.

### Q4: How do I re-run a failed CI pipeline?
- Pushing a new commit to your PR branch automatically triggers a fresh CI run.
- Alternatively, authorized operators can trigger `universal-ci-pipeline` in Jenkins with parameters: `APPLICATION`, `TARGET_ENV`, `GIT_BRANCH`, and `COMMIT_SHA`.
