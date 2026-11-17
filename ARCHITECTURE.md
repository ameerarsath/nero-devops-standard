# NERO ENTERPRISE DEVOPS STANDARD — ARCHITECTURE SPECIFICATION

Version: `1.2.0-phase4`  
Scope: Multi-Cloud, Multi-Account Universal Application Delivery Framework  

---

## 1. Core Architectural Tenets

The **Nero Enterprise DevOps Standard** is structured around five foundational architecture principles:

1. **Application Independence (Universal Delivery Engine)**:
   - The platform engine does not contain hardcoded assumptions about specific programming languages, frameworks, or database engines.
   - Applications provide a declarative `app.spec.yaml`. The platform interprets this specification to select the appropriate build, infrastructure, deployment, and verification adapters.

2. **Immutable Release Packaging ("Build Once, Promote Everywhere")**:
   - Rebuilding source code in every environment causes configuration drift and dependency non-determinism.
   - The Nero standard builds artifacts once in `develop`.
   - The output is an immutable `release-manifest.json` binding components to full 64-character SHA-256 digests (`sha256:...`).
   - Higher environments (`qa`, `prod`, `canary`) strictly verify and deploy the pre-existing digest without recompiling.

3. **Multi-Platform & Multi-Topology Abstraction**:
   - The platform supports two infrastructure planes:
     - **`floci-local`**: High-fidelity local simulation using Floci / LocalStack and local Docker Engine (Zero Cloud Cost).
     - **`aws`**: Real AWS Cloud targeting Amazon ECS Fargate, S3, Application Load Balancers, and RDS.
   - The platform supports two account topologies:
     - **`multi_account`**: Complete AWS account isolation via AWS Organizations and STS AssumeRole.
     - **`single_account`**: Resource-prefix and tag-based namespace isolation within a shared account.

4. **Cryptographic Tamper-Evident Audit Logging**:
   - Every operational event (Build, Plan, Apply, Deploy, Verify, Rollback, Governance Approval) is hashed with SHA-256 and chained to the previous record's hash.
   - Creates a verifiable ledger that proves deployment compliance and detects any offline tampering.

5. **Fail-Closed Security & Governance**:
   - Strict separation of duties: Production deployments require independent QA sign-off and SRE Change Ticket authorization (`CHG-*`).
   - Workloads are strictly forbidden from deploying directly to the AWS Organizations Management Account.

---

## 2. Component Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                            APPLICATION WORKSPACE                                  |
|                                                                                   |
|   +------------------------------------+  +------------------------------------+  |
|   |          app.spec.yaml             |  |      platform_config.yaml          |  |
|   |  - Metadata & Ownership            |  |  - Active Clouds (Floci / AWS)     |  |
|   |  - Components & Ports              |  |  - Supported Environments          |  |
|   |  - Dependencies & Secrets          |  |  - Security & Account Policies     |  |
|   +-----------------+------------------+  +-----------------+------------------+  |
+---------------------|---------------------------------------|---------------------+
                      |                                       |
                      v                                       v
+-----------------------------------------------------------------------------------+
|                        NERO PLATFORM CORE ENGINE (Python)                         |
|                                                                                   |
|   +---------------------------------------------------------------------------+   |
|   |                             Platform CLI                                  |   |
|   |   validate | check-catalog | resolve | build-release | deploy | verify     |   |
|   +-------------------------------------+-------------------------------------+   |
|                                         |                                         |
|         +-------------------------------+-------------------------------+         |
|         |                               |                               |         |
|         v                               v                               v         |
|   +-------------+               +---------------+               +-------------+   |
|   | Spec Parser |               | Env Resolver  |               | Catalog Reg |   |
|   | & Validator |               | Multi-Cloud   |               | Trust Guard |   |
|   +-------------+               +---------------+               +-------------+   |
|                                         |                                         |
|   +-------------------------------------+-------------------------------------+   |
|   |                        Universal Orchestrator                             |   |
|   |  - Release Manifest Generator       - Immutable Digest Verifier           |   |
|   |  - Emergency Rollback Coordinator   - Cryptographic Audit Logger          |   |
|   +-------------------------------------+-------------------------------------+   |
+-----------------------------------------|-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                               PLUG-IN ADAPTERS                                    |
|                                                                                   |
|   +------------------+  +------------------+  +----------------+  +-----------+   |
|   |  Build Adapters  |  | Deploy Adapters  |  | Infra Adapters |  | Verifiers |   |
|   |  - Dockerfile    |  |  - ECS Fargate   |  |  - Terraform   |  | - Health  |   |
|   |  - Node Frontend |  |  - S3 Static     |  |    Modules     |  | - Assets  |   |
|   +------------------+  +------------------+  +----------------+  +-----------+   |
+-----------------------------------------|-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                         TARGET INFRASTRUCTURE TARGETS                             |
|                                                                                   |
|    [LOCAL EMULATION (Floci)]                      [REAL AWS CLOUD]                |
|    - Local Floci Container (4566)                 - AWS ECS Fargate               |
|    - Host Docker Daemon Engine                    - Amazon S3 + CloudFront        |
|    - Port Mappings: 8091, 8095, 8085              - RDS PostgreSQL Multi-AZ       |
|    - Simulated Accounts (111122223333)            - AWS Secrets Manager & STS     |
+-----------------------------------------------------------------------------------+
```

---

## 3. The Golden Path Lifecycle

Every application deployment follows 8 deterministic phases:

1. **Phase 1: Preflight & Central Catalog Authorization**:
   - Confirms that the requesting application ID, branch, target environment, platform, and requested adapters are explicitly permitted in `platform_core/catalog/applications.yaml`.
2. **Phase 2: Context & Topology Resolution**:
   - Resolves target AWS accounts, STS deployment role ARNs, Secrets Manager names, resource prefixes, and port mappings.
3. **Phase 3: Immutable Build & Release**:
   - Builds artifacts or, if a valid `RELEASE_ID` is provided, stages existing release manifests with zero recompilation.
4. **Phase 4: Infrastructure Planning (Terraform Plan)**:
   - Validates syntax, imports pre-existing secrets idempotently, and generates immutable Terraform execution plans.
5. **Phase 5: Production Governance Gates**:
   - Enforces two-person separation of duties (QA Technical Sign-off + Operations Change Ticket) before production execution.
6. **Phase 6: Infrastructure Execution (Terraform Apply)**:
   - Applies the pre-approved plan.
7. **Phase 7: Workload Deployment**:
   - Dispatches container workloads to ECS (or Floci container runtime) and syncs static assets to S3 buckets.
8. **Phase 8: Synthetic Health Verification**:
   - Executes automated HTTP probes against backend health endpoints (strictly enforcing HTTP 200) and deep asset inspection on S3.
   - Appends cryptographically chained event to `audit_log.jsonl`.

---

## 4. Master Architectural Blueprint & Governance Documents

For the complete product requirements, DevSecOps threat model, architectural decision records, and multi-phase implementation roadmaps, consult the authoritative documentation under `docs/architecture/`:

- **Master Architecture Blueprint**:  
  [`UNIVERSAL_ENTERPRISE_DEVOPS_AUTOMATION_PLATFORM_BLUEPRINT.md`](docs/architecture/UNIVERSAL_ENTERPRISE_DEVOPS_AUTOMATION_PLATFORM_BLUEPRINT.md)  
  *Covers Product Vision, Scope, Functional Requirements (APP, CI, BLD, REL, IAC, DEP, PROMO, TST, SEC), System Layers (1-10), and Governance.*
- **DevSecOps Threat Model**:  
  [`THREAT_MODEL.md`](docs/architecture/THREAT_MODEL.md)  
  *STRIDE threat analysis, Docker socket privilege isolation, secret protection, and AI boundary guardrails.*
- **Architecture Decision Records (ADRs)**:  
  [`ADR_INDEX.md`](docs/architecture/adr/ADR_INDEX.md)  
  - `ADR-001`: Deterministic DevOps Automation Before AI Intelligence
  - `ADR-002`: Central Application Catalog & Declarative Application Specifications
  - `ADR-003`: Immutable Release Packaging & Zero-Rebuild Promotion
  - `ADR-004`: Hybrid Execution Architecture & Typed Adapter Contracts
  - `ADR-005`: Two-Person Production Governance & Cryptographic Audit Hash Chaining
- **Programme 1 Roadmap (Deterministic DevOps Automation)**:  
  [`NON_AI_ROADMAP_A0_A9.md`](docs/architecture/NON_AI_ROADMAP_A0_A9.md)  
  *Execution plan for Phases A0 through A9.*
- **Programme 2 Roadmap (AI-Enhanced DevOps)**:  
  [`AI_ENHANCED_DEVOPS_ROADMAP_B0_B6.md`](docs/architecture/AI_ENHANCED_DEVOPS_ROADMAP_B0_B6.md)  
  *Evolution plan for Phases B0 through B6 with Autonomy Tiers (Levels 1 to 5).*

