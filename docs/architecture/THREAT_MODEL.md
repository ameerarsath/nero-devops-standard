# Enterprise DevSecOps Threat Model
## Nero Universal DevOps Automation Platform

**Document Identifier:** `NERO-SEC-TM-001`  
**Classification:** Internal Engineering & Security Architecture  
**Scope:** `nero_devops_standard` Platform Core, Jenkins Pipelines, Floci Simulation, and Target Cloud Runtimes  

---

## 1. Executive Summary

This threat model identifies high-impact security risks across the software delivery lifecycle and details the platform's fail-closed architectural controls. The model adheres to the **STRIDE** methodology (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege) and emphasizes the security boundaries between deterministic CI/CD automation and future AI intelligence layers.

---

## 2. Threat Analysis & Mitigation Matrix

### 2.1 Threat Category: Elevation of Privilege via Docker Socket
- **Threat Vector**: Pipeline jobs mounting `/var/run/docker.sock` inside the Jenkins container can potentially execute arbitrary root commands on the host operating system.
- **Risk Level**: **HIGH**
- **Platform Mitigations**:
  - All containerized workloads run with non-root user IDs (`USER 10001:10001` or `USER node` / `USER appuser`).
  - Container capabilities are explicitly dropped (`--cap-drop=ALL`).
  - Long-term roadmap (Phase A4): Transition Jenkins builds to isolated, ephemeral Kaniko / Sysbox container build workers that do not require privileged host socket mounts.

### 2.2 Threat Category: Information Disclosure of Secrets & Credentials
- **Threat Vector**: Plaintext database passwords, JWT signing keys, or API tokens committed to Git, embedded in Docker images, written to release manifests, or exposed in Jenkins console logs.
- **Risk Level**: **CRITICAL**
- **Platform Mitigations**:
  - `release-manifest.json` schema strictly forbids secret fields.
  - Secrets are injected dynamically at container launch via AWS Secrets Manager / Floci Secrets Manager integration.
  - Preflight checks scan repositories for secrets using Gitleaks/Trufflehog rules.
  - Jenkins environment variables are masked (`TF_IN_AUTOMATION=true`, credential wrappers).

### 2.3 Threat Category: Tampering & Supply Chain Attacks
- **Threat Vector**: Rebuilding artifacts in QA/Production leading to unauthorized code tampering, malicious package replacement in npm/Maven, or unverified Docker image tags (`:latest` mutations).
- **Risk Level**: **CRITICAL**
- **Platform Mitigations**:
  - Enforced "Build Once, Promote Everywhere" pattern: images are pinned to 64-character SHA-256 digests (`@sha256:...`).
  - Lockfile enforcement (`package-lock.json`, `pom.xml`); open-ended version ranges fail validation.
  - Generation of CycloneDX Software Bill of Materials (SBOM) and SLSA-compliant build provenance.

### 2.4 Threat Category: Repudiation of Operational & Deployment Changes
- **Threat Vector**: Malicious or unauthorized operator making destructive production changes or altering deployment logs retroactively.
- **Risk Level**: **HIGH**
- **Platform Mitigations**:
  - Every action (Build, Plan, Apply, Deploy, Rollback, Approval) writes to `audit_log.jsonl`.
  - Cryptographic hash chaining: Each event includes a SHA-256 hash calculated over its canonical JSON content and the previous event's hash.
  - Independent validation CLI (`verify_audit_ledger`) detects any deleted, reordered, or modified log entries.

### 2.5 Threat Category: Spoofing of Production Governance Approvals
- **Threat Vector**: Developer self-approving a production change, bypassing Change Advisory Board (CAB) review, or using an unauthenticated command-line parameter.
- **Risk Level**: **HIGH**
- **Platform Mitigations**:
  - Two-Person Governance Gate: Requires two distinct authenticated individuals (`qa.lead` and `sre.lead`).
  - Separation of duties enforcement: If `qa_approver == ops_approver`, the pipeline halts with `[GOVERNANCE_VIOLATION]`.
  - Mandatory ITIL change ticket format validation (`CHG-*`).

### 2.6 Threat Category: Account Boundary Confusion (Floci Simulation vs Real AWS)
- **Threat Vector**: Treating Floci simulated account IDs (`111122223333`, `444455556666`, `777788889999`) as real AWS IAM accounts, or accidentally deploying unverified workloads to live AWS management accounts.
- **Risk Level**: **MEDIUM**
- **Platform Mitigations**:
  - Explicit platform selection (`floci` vs `aws`) in `platform_config.yaml`.
  - Real AWS execution requires explicit provider authorization and AWS profile activation.
  - Strict policy guard preventing workloads from ever targeting the AWS Organizations Management Account.

---

## 3. AI Safety and Boundary Guardrails (Programme 2)

As the platform introduces AI capabilities in Programme 2, the following boundary rules are strictly enforced:

1. **AI is Never an Authority**: AI agents cannot authenticate users, authorize production releases, decrypt secrets, or bypass Terraform plan reviews.
2. **Schema & Policy Validation**: All structured proposals generated by AI agents must pass through Pydantic schema validation and deterministic policy engines.
3. **Prompt Injection Defense**: Retrieved logs, commits, and error messages are treated as untrusted data; LLM prompts isolate raw log inputs to prevent prompt injection attacks.
4. **Audit Trail of AI Actions**: Every AI recommendation, diagnosis, and bounded action is cryptographically recorded in `audit_log.jsonl` under action `AI_AGENT_ACTION`.
5. **Human in the Loop**: Any destructive, state-modifying, or production operation proposed by AI strictly requires human authorization under Autonomy Levels 3-5.
