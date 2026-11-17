# NERO ENTERPRISE DEVOPS STANDARD
## Universal Application Delivery & Cloud Governance Framework

Version: `1.2.0-phase4`  
Author: Enterprise Platform Architecture & DevSecOps Engineering  

---

## 1. Overview & Mission

The **Nero DevOps Standard** is a battle-tested, application-independent Universal Delivery Platform designed to provide a single, hardened Golden Path for building, provisioning, deploying, verifying, and rolling back applications across multi-account AWS cloud environments and local Floci/LocalStack emulators.

### Core Guiding Principle:
> **"Build once, create an immutable release, deploy it through the Floci/AWS environments, verify it, promote the same release, and demonstrate rollback without rebuilding."**

Any application—whether a Node.js Express REST API, a Python asynchronous worker, a Spring Boot microservice, or a React Single Page Application—can integrate with this standard simply by declaring an `app.spec.yaml` without writing custom CI/CD pipelines or reinventing deployment automation.

---

## 2. Directory Structure

```
nero_devops_standard/
├── README.md                                 # Standard guide & CLI reference (this file)
├── ONBOARDING.md                             # 10-Minute application onboarding guide
├── ARCHITECTURE.md                           # Enterprise multi-cloud architecture specification
├── platform_config.yaml                      # Central platform environment configuration
│
├── docs/                                     # Architecture specifications & qualification reports
│   ├── architecture/                         # Architecture blueprint, ADRs, Threat Model, Roadmaps
│   │   ├── UNIVERSAL_ENTERPRISE_DEVOPS_AUTOMATION_PLATFORM_BLUEPRINT.md # Master Architecture Blueprint
│   │   ├── THREAT_MODEL.md                   # DevSecOps STRIDE threat model & AI boundaries
│   │   ├── NON_AI_ROADMAP_A0_A9.md           # Programme 1 execution roadmap (Phases A0 to A9)
│   │   ├── AI_ENHANCED_DEVOPS_ROADMAP_B0_B6.md# Programme 2 AI evolution roadmap (Phases B0 to B6)
│   │   └── adr/                              # Architecture Decision Records
│   │       ├── ADR_INDEX.md                  # ADR index table
│   │       ├── ADR-001_DETERMINISTIC_FIRST_STRATEGY.md
│   │       ├── ADR-002_CENTRAL_CATALOG_AND_DECLARATIVE_SPEC.md
│   │       ├── ADR-003_IMMUTABLE_RELEASE_AND_ZERO_REBUILD.md
│   │       ├── ADR-004_HYBRID_EXECUTION_AND_ADAPTER_CONTRACT.md
│   │       └── ADR-005_TWO_PERSON_GOVERNANCE_AND_AUDIT_CHAIN.md
│   └── phase4_stage1_3_qualification_report.md
│
├── platform_core/                            # Core Platform Python Engine
│   ├── engine/                               # Platform CLI, Orchestrator, Resolver, Parser
│   │   ├── cli.py                            # Unified CLI interface for CI/CD & developers
│   │   ├── orchestrator.py                   # Golden Path build, release, deploy & rollback
│   │   ├── resolver.py                       # Environment context & security boundary resolver
│   │   ├── parser.py                         # app.spec.yaml parser & schema validator
│   │   ├── models.py                         # Pydantic models for application specifications
│   │   └── errors.py                         # Enterprise error hierarchy and status codes
│   ├── adapters/                             # Plug-and-Play technology adapters
│   │   ├── build/                            # Dockerfile & Node.js frontend packaging
│   │   ├── deployment/                       # ECS container & S3 static deployment
│   │   ├── infrastructure/                   # Terraform plan/apply & secret import
│   │   └── verification/                     # Automated synthetic health verification
│   ├── catalog/                              # Central Application Trust Registry
│   │   ├── applications.yaml                 # Approved application definitions & guardrails
│   │   └── schema/                           # JSON schemas for specs & platform config
│   ├── audit/                                # Immutable cryptographically chained audit ledger
│   │   ├── audit_verifier.py                 # SHA-256 chain verification tool
│   │   └── audit_log.jsonl                   # Chained audit event log
│   ├── policy/                               # Non-root, runtime & container security policies
│   └── tests/                                # Platform core unit test suite
│
├── ci-cd/                                    # Universal CI/CD Pipelines
│   ├── jenkins/pipelines/universal/
│   │   └── Jenkinsfile                       # Universal Declarative Pipeline
│   └── scripts/
│       ├── create_universal_job.py           # Registers the universal job in Jenkins
│       └── trigger_and_follow_pipeline.py    # Pipeline automation test runner
│
├── infrastructure/terraform/modules/         # Reusable Infrastructure Modules
│   ├── ecs_backend/                          # Reusable ECS Fargate container service
│   ├── s3_website/                           # Static website hosting S3 module
│   ├── s3_bucket/                            # General S3 storage bucket module
│   ├── rds_postgres/                         # Managed PostgreSQL RDS database
│   ├── sqs_queue/                            # Standard SQS message queue
│   ├── secrets/                              # AWS Secrets Manager secret module
│   ├── alb/                                  # Application Load Balancer
│   ├── vpc/                                  # Multi-AZ isolated VPC network
│   └── cloudfront_frontend/                  # CloudFront CDN distribution
│
├── templates/                                # Ready-to-copy application starter templates
│   ├── app.spec.template.yaml                # Starter specification template
│   ├── microservice-node/                    # Node.js Express REST API template
│   ├── background-worker-python/             # Python background worker template
│   └── fullstack-polyglot/                   # Fullstack polyglot application template
│
├── tests/                                    # End-to-End Compliance & Failure Test Suite
│   ├── failure/                              # Failure injection and corruption resilience
│   ├── security/                             # IAM guardrails & tamper detection
│   └── integration/                          # Terraform state isolation tests
│
└── docs/                                     # Architecture specifications & qualification reports
    └── phase4_stage1_3_qualification_report.md
```

---

## 3. Platform Capabilities

1. **Universal Build & Immutable Release Engine**:
   - Compiles container images and static bundles into an immutable `release-manifest.json`.
   - Records full 64-character SHA-256 digests (`sha256:...`) for OCI images and artifact tarballs.
   - Enforces zero recompilation during promotion from `develop` to `qa` to `prod`.

2. **Automated Multi-Cloud Resolution**:
   - Resolves deployment parameters dynamically based on `--platform` (`floci-local` or `aws`) and `--topology` (`multi_account` or `single_account`).
   - Generates environment variables, AWS account IDs, STS AssumeRole ARNs, Secrets Manager names, and health endpoints without hardcoding.

3. **Controlled Rollback with Governance**:
   - Emergency rollback command stages any previous verified release manifest with zero rebuild.
   - Validates ITIL change tickets (`CHG-*`, `INC-*`, `HOTFIX-*`) and logs immutable audit records.

4. **Cryptographic Audit Ledger**:
   - Every build, plan, deploy, verification, governance approval, and rollback is recorded in `platform_core/audit/audit_log.jsonl`.
   - Every record links to the SHA-256 hash of its predecessor:
     $$\text{record\_hash}_i = \text{SHA256}(\text{record}_i \parallel \text{record\_hash}_{i-1})$$
   - Any tampering or log deletion is instantly detected by `verify_audit_ledger()`.

5. **Universal Jenkins Pipeline**:
   - Single pipeline (`universal-application-pipeline`) handles all applications registered in the catalog.
   - Parameterized by `APPLICATION`, `ENVIRONMENT`, `TARGET_PLATFORM`, `ACCOUNT_TOPOLOGY`, `ACTION`, and `RELEASE_ID`.
   - Integrates two-person governance gates (QA Lead sign-off + SRE Change Ticket) for production releases.

---

## 4. Platform Engine CLI Reference

The core platform CLI is located at `platform_core/engine/cli.py`.

```bash
# 1. Validate application specification
python -m platform_core.engine.cli validate --spec app.spec.yaml

# 2. Check application authorization in catalog
python -m platform_core.engine.cli check-catalog \
    --app my-service \
    --env develop \
    --platform floci-local \
    --topology multi_account \
    --spec app.spec.yaml

# 3. Resolve environment context
python -m platform_core.engine.cli resolve \
    --app my-service \
    --env develop \
    --platform floci-local \
    --topology multi_account \
    --format shell

# 4. Build or promote immutable release
python -m platform_core.engine.cli build-release \
    --app my-service \
    --spec app.spec.yaml \
    --release-id rel-my-service-01

# 5. Cryptographically validate release manifest
python -m platform_core.engine.cli validate-manifest \
    --app my-service \
    --manifest release-manifest.json

# 6. Deploy container workload
python -m platform_core.engine.cli deploy-container \
    --app my-service \
    --env develop \
    --platform floci-local \
    --topology multi_account \
    --component api \
    --image api:rel-my-service-01 \
    --host-port 8091

# 7. Deploy frontend static assets to S3
python -m platform_core.engine.cli deploy-frontend \
    --app my-service \
    --env develop \
    --platform floci-local \
    --topology multi_account \
    --dist dist

# 8. Synthetic health verification
python -m platform_core.engine.cli verify \
    --app my-service \
    --env develop \
    --platform floci-local \
    --topology multi_account

# 9. Emergency zero-rebuild rollback
python -m platform_core.engine.cli rollback \
    --app my-service \
    --env qa \
    --release-id rel-my-service-01 \
    --operator sops-admin \
    --ticket CHG-20261107-ROLLBACK \
    --reason "Restoring previous stable release"
```

---

## 5. Verification & Compliance Testing

The framework includes 57 automated tests covering security, state isolation, and failure injection:

```bash
# Run entire test suite
python -m pytest tests/ platform_core/tests/

# Verify cryptographic audit chain integrity
python -c "from platform_core.audit.audit_verifier import verify_audit_ledger; print(verify_audit_ledger('platform_core/audit/audit_log.jsonl'))"
```
