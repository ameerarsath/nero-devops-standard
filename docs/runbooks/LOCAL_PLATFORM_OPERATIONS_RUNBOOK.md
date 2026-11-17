# NERO Universal Enterprise DevOps Automation Platform
## Local Platform Operations Runbook

**Document Type:** Platform Operations Runbook & Operational Standard  
**Document ID:** NERO-RUNBOOK-001  
**Programme:** NERO Programme 1 — Deterministic DevOps Automation  
**Phase:** Phase A1 (Platform Foundation & Qualification)  
**Execution Target:** Local Platform (Floci / Docker Engine / Local OCI Registry)  
**Security Classification:** Enterprise Internal / Developer Reference  
**Effective Date:** 2026-11-08  
**Status:** Authoritative  

---

## 1. System Overview & Architecture Topology

The NERO Local Platform executes the complete end-to-end software delivery lifecycle deterministically on local infrastructure without requiring real cloud credentials or incurring cloud expenditure ($0.00).

```
                      +------------------------------------------+
                      |        Universal Jenkins Pipeline        |
                      |          (http://localhost:8080)         |
                      +---------------------+--------------------+
                                            |
                                            v
+---------------------------------------------------------------------------------------+
|                                    NERO Engine                                        |
|   (app.spec.yaml -> Resolver -> Policy Enforcer -> Adapter Facade -> Audit Ledger)   |
+--------+------------------+-------------------+--------------------+------------------+
         |                  |                   |                    |
         v                  v                   v                    v
+-----------------+  +----------------+  +-------------------+  +------------------------+
| Local OCI Reg   |  | Floci Platform |  | Docker Engine     |  | Cryptographic Ledger   |
| localhost:5100  |  | localhost:4566 |  | ECS Container Sim |  | SHA-256 Hash Chain     |
| Docker Registry |  | S3/IAM Mock    |  | Ports 8085-8089   |  | audit_log.jsonl        |
+-----------------+  +----------------+  +-------------------+  +------------------------+
```

---

## 2. Platform Port Matrix & Container Inventory

| Service Name | Container / Host Name | Port | Protocol | Purpose / Description |
|---|---|---|---|---|
| **Jenkins Controller** | `jenkins` | `8080` | HTTP | Declarative CI/CD pipeline orchestrator |
| **Floci Platform Core** | `floci-local` | `4566` | HTTP | S3 bucket simulation & IAM mock endpoints |
| **Local OCI Registry** | `floci-aws-ecr-registry` | `5100` | HTTP | Distribution v2 OCI container image registry |
| **PostgreSQL DB** | `billing-postgres` | `5432` | TCP | Relational database instance |
| **Backend (Develop)** | `hotel-billing-backend-develop` | `8085` | HTTP | Development environment ECS container |
| **Backend (QA)** | `hotel-billing-backend-qa` | `8087` | HTTP | QA environment ECS container |
| **Backend (Prod)** | `hotel-billing-backend-prod` | `8089` | HTTP | Production environment ECS container |

---

## 3. Preflight Health Verification

Before running deployment pipelines, verify all platform subsystems are operational:

### 3.1 Ping OCI Registry
```powershell
curl http://localhost:5100/v2/
# Expected response: {} with HTTP 200 OK
```

### 3.2 Verify Floci Simulator
```powershell
curl http://localhost:4566/_localstack/health
# S3 and IAM features should report available
```

### 3.3 Verify Baseline Terraform State Preservation
Ensure the local baseline Terraform state file has not been altered:
```powershell
python -c "import json; data=json.load(open('infrastructure/terraform/environments/local/terraform.tfstate')); assert data['serial'] == 23 and len(data['resources']) == 15; print('[PASS] State baseline intact (Serial 23, 15 resources)')"
```

### 3.4 Run Comprehensive Platform Qualification
```powershell
$env:PYTHONPATH="."
python tests/run_platform_qualification.py
# Expected output: >>> NERO PROGRAMME 1 — PHASE A1 QUALIFICATION: PASSED (100%) <<<
```

---

## 4. Deterministic Platform CLI Operations

All platform operations are executed via typed CLI commands in `platform_core.engine.cli`.

### 4.1 Validate Application Specification
Validates the declarative `app.spec.yaml` against schema constraints and catalog rules:
```powershell
python -m platform_core.engine.cli validate-spec --spec-file app.spec.yaml
```

### 4.2 Build & Release Artifacts
Builds container images with non-root security enforcement, creates release manifests, and signs image digests:
```powershell
python -m platform_core.engine.cli build-and-release `
  --spec-file app.spec.yaml `
  --release-id rel-20261108-01 `
  --source-repo https://github.com/ameerarsath/billing-system.git `
  --source-commit 3bf604266b4f233c3899d0e315a0538812542b04
```

### 4.3 Plan Infrastructure
Executes preflight `terraform fmt -check`, `terraform validate`, creates state backups, and produces binary plan files:
```powershell
python -m platform_core.engine.cli plan-infra `
  --app-id hotel-billing `
  --environment develop `
  --target-platform floci
```

### 4.4 Apply Infrastructure
Safely applies approved Terraform plans with pre-apply state snapshotting:
```powershell
python -m platform_core.engine.cli apply-infra `
  --app-id hotel-billing `
  --environment develop `
  --target-platform floci
```

### 4.5 Deploy Application Workload
Deploys frontend static assets to S3 and backend container to ECS simulation with automatic port conflict self-healing:
```powershell
python -m platform_core.engine.cli deploy `
  --app-id hotel-billing `
  --environment develop `
  --target-platform floci `
  --component-name backend `
  --host-port 8085
```

### 4.6 Verify Deployment Health
Executes synthetic probes enforcing strict HTTP 200 responses and configurable exponential backoff:
```powershell
python -m platform_core.engine.cli verify `
  --app-id hotel-billing `
  --environment develop `
  --target-platform floci
```

### 4.7 Zero-Rebuild Instant Rollback
Reverts running containers to a previous release manifest digest without re-running build steps:
```powershell
python -m platform_core.engine.cli rollback `
  --app-id hotel-billing `
  --environment develop `
  --target-platform floci `
  --target-manifest release-manifest.json
```

### 4.8 Two-Person Governed Emergency Deploy ("Break-Glass")
Executes emergency production deployment requiring dual cryptographic approvers and valid `CHG-*` change tickets:
```powershell
python -m platform_core.engine.cli break-glass-deploy `
  --app-id hotel-billing `
  --environment prod `
  --target-platform floci `
  --approver-1 devops-lead-01 `
  --approver-2 sec-officer-02 `
  --ticket CHG-998822
```

---

## 5. Security & Governance Operations

### 5.1 Cryptographic Audit Ledger Verification
The audit ledger `platform_core/audit/audit_log.jsonl` implements a tamper-evident SHA-256 hash chain:
```powershell
python platform_core/audit/audit_verifier.py
```

### 5.2 Generate Signed Audit Checkpoint
Generates an HMAC-SHA256 signature pinning the ledger head to prevent complete log replacement attacks:
```powershell
python platform_core/audit/audit_verifier.py --checkpoint
```

### 5.3 Deterministic Exit Codes
When running automated scripts, the CLI emits standardized exit codes:
- `0`: Success
- `10`: Specification validation error (`SpecError`)
- `15`: Application catalog rejection (`CatalogError`)
- `20`: Security policy violation (`PolicyError`)
- `30`: Infrastructure planning/apply failure (`InfraError`)
- `40`: Deployment failure (`DeployError`)
- `50`: Deployment verification failure (`VerifyError`)
- `60`: Governance policy violation (`GovernanceError`)

---

## 6. Troubleshooting & Operational Runbooks

### Recipe A: Host Port Conflict Self-Healing
*Symptoms:* `Error starting userland proxy: listen tcp4 0.0.0.0:8085: bind: address already in use`  
*Action:*
The NERO ECS deployment adapter (`platform_core/adapters/deployment/ecs_adapter.py`) automatically discovers any existing container bound to the target host port, cleanly stops and removes it, and re-allocates the port.
To inspect manually:
```powershell
docker ps --filter publish=8085
docker stop <container_id>
```

### Recipe B: Local OCI Registry Unreachable
*Symptoms:* `urllib.error.URLError: Connection refused on localhost:5100`  
*Action:*
Verify `floci-aws-ecr-registry` is running:
```powershell
docker ps --filter name=floci-aws-ecr-registry
# If stopped, restart:
docker restart floci-aws-ecr-registry
```

### Recipe C: Terraform State Backup Restoration
*Symptoms:* Corrupted local state during testing  
*Action:*
Use the automated state backup utility:
```powershell
python infrastructure/terraform/scripts/backup_states.py --restore develop
```
Or manually copy the latest snapshot from `infrastructure/terraform/environments/<env>/.state_backups/`.

---

## 7. Operational Sign-Off & Verification

This runbook has been qualified under NERO Programme 1 — Phase A1. All operational instructions and commands have been verified against active local runtime components.
