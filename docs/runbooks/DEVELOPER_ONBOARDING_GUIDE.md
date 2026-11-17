# NERO ENTERPRISE DEVOPS AUTOMATION PLATFORM
## Developer Onboarding & Application Integration Runbook (Programme 1 — Phase A2)

---

## 1. Executive Summary & Architecture Principles

The **NERO Universal Enterprise DevOps Automation Platform** eliminates bespoke CI/CD pipelines, hardcoded application logic, and manual infrastructure orchestration. 

Under **Programme 1 (Deterministic Automation)**, any application across any technology stack (Java, Node.js, Python, Go, polyglot) can onboard onto the enterprise delivery lifecycle by providing a single declarative contract: [`app.spec.yaml`](file:///d:/project/billing-system-master/billing-system-master/app.spec.yaml).

### Core Architectural Guarantees:
1. **Universal Declarative Abstraction**: Single parameterized Jenkinsfile executes all delivery stages dynamically. No application-specific branches, pipelines, or conditional hacks.
2. **Build Once, Promote Everywhere**: Container images and static assets are compiled once in the release stage, cryptographically signed, and promoted across `develop`, `qa`, and `prod` with zero rebuild.
3. **Fail-Closed Security & Non-Root Enforcement**: All runtime containers must declare an explicit non-root user (`UID != 0`). Unpinned dependencies, missing lockfiles, or EOL runtimes fail closed.
4. **Deterministic Port Isolation**: Port allocations across environments are managed automatically by the platform to guarantee collision-free local and cluster simulation.

---

## 2. The Application Specification (`app.spec.yaml`)

Every onboarded service defines its topology, build instructions, runtime requirements, and dependencies in `app.spec.yaml`.

### Complete Specification Reference (Schema v2)

```yaml
apiVersion: platform.nero/v1 # or platform.enterprise.com/v2
kind: Application

metadata:
  id: sample-service
  name: sample-service
  version: "1.0.0"
  description: "Enterprise Microservice"
  owner: "team-core@enterprise.com"
  team: "core-engineering"
  repository: "https://github.com/enterprise/sample-service.git"
  securityTier: "tier-2-standard" # tier-1-business-critical | tier-2-standard
  labels:
    service_type: "api"
    compliance: "sox-compliant"

spec:
  components:
    - name: api
      type: container-service # container-service | static-site | worker
      source:
        context: "."
        dockerfile: "Dockerfile"
      build:
        adapter: "go" # go | node | dockerfile | python
        target_stage: "runtime"
      runtime:
        name: "go"
        version: "1.27.3"
        base_image: "gcr.io/distroless/static-debian12:nonroot"
        lockfile: "go.mod"
        port: 8080
        cpu_units: 256
        memory_mb: 256
        health_check:
          path: "/health"
          type: "http"
          interval_seconds: 15
          timeout_seconds: 5
          healthy_threshold: 2
      deployment:
        adapter: "ecs" # ecs | s3-static
        desired_count: 1
        strategy: "rolling"
        local_port: 8100 # Optional fixed port or auto-allocated by catalog

  dependencies:
    - name: primary-db
      type: "rds-postgres"
      engine_version: "15"
      allocated_storage_gb: 20

  secrets:
    schema:
      - name: "database.password"
        description: "Primary database credential"
        required: true
```

---

## 3. Step-by-Step Onboarding Walkthrough

### Step 1: Automatic Repository Inspection

The platform provides a non-intrusive static code inspection engine that analyzes project structure, detects languages, frameworks, lockfiles, and generates a valid candidate `app.spec.yaml`:

```bash
# From workspace root:
python -m platform_core.engine.cli inspect-repo \
  --dir path/to/your/repo \
  --emit-candidate path/to/your/repo/app.spec.yaml \
  --app your-service-id
```

**What the inspector detects:**
- **Go**: `go.mod`, `go.sum`, detects Gin/net-http, configures Go 1.27.3 multi-stage distroless build.
- **Node.js**: `package.json`, `package-lock.json`, detects Express APIs vs. Vite/React SPAs.
- **Python**: `requirements.txt`, `pyproject.toml`, detects FastAPI/Flask APIs vs. background queue consumers.
- **Java**: `pom.xml`, Maven/Gradle Spring Boot microservices.

### Step 2: Validate the Specification

Validate your specification against the platform Pydantic v2 schema and AST confinement rules:

```bash
python -m platform_core.engine.cli validate --spec path/to/your/repo/app.spec.yaml
```

*Expected output:*
```text
[OK] Application Specification 'your-service-id' v1.0.0 is VALID.
     Components: ['api']
     Dependencies: []
```

### Step 3: Register Application in Central Catalog

Register the application in the Central Application Catalog ([`platform_core/catalog/applications.yaml`](file:///d:/project/billing-system-master/billing-system-master/platform_core/catalog/applications.yaml)):

```bash
python -m platform_core.engine.cli onboard-app \
  --spec path/to/your/repo/app.spec.yaml \
  --repo https://github.com/enterprise/your-service.git \
  --security-tier tier-2-standard
```

*The catalog manager will automatically assign collision-free host ports across `develop`, `qa`, and `prod`.*

### Step 4: Verify Catalog Registration & Environment Resolution

Check authorization and preview runtime parameters:

```bash
# Catalog check:
python -m platform_core.engine.cli check-catalog \
  --app your-service-id \
  --env develop \
  --platform floci \
  --topology multi_account

# Environment resolution:
python -m platform_core.engine.cli resolve \
  --app your-service-id \
  --env develop \
  --platform floci
```

### Step 5: Test Build & Release Locally

Run the platform build engine to compile artifacts, generate SBOM/provenance references, and output the cryptographic release manifest:

```bash
python -m platform_core.engine.cli build-release \
  --app your-service-id \
  --spec path/to/your/repo/app.spec.yaml
```

*Outputs [`release-manifest.json`](file:///d:/project/billing-system-master/billing-system-master/release-manifest.json) containing SHA-256 digests and provenance records.*

### Step 6: Deploy & Verify Locally (Floci Simulation)

Deploy the container workload to the local Floci cluster:

```bash
# Deploy container:
python -m platform_core.engine.cli deploy-container \
  --app your-service-id \
  --env develop \
  --platform floci

# Synthetic health check:
python -m platform_core.engine.cli verify \
  --app your-service-id \
  --env develop \
  --platform floci
```

---

## 4. Reference Applications Catalog

The platform provides 4 production-ready reference implementations:

| Application ID | Architecture / Stack | Build Adapter | Ports (Dev/QA/Prod) | Reference Location |
| :--- | :--- | :--- | :--- | :--- |
| **`hotel-billing`** | Java 17 Spring Boot + React 19 Vite + PostgreSQL | `dockerfile` / `node` | 8085 / 8087 / 8089 | [`app.spec.yaml`](file:///d:/project/billing-system-master/billing-system-master/app.spec.yaml) |
| **`sample-node-service`** | Node.js 22 Express REST API | `dockerfile` / `node` | 8091 / 8092 / 8093 | [`applications/sample-node-service/`](file:///d:/project/billing-system-master/billing-system-master/applications/sample-node-service) |
| **`sample-python-worker`** | Python 3.12 Queue Worker + SQS fallback | `dockerfile` / `python` | 8095 / 8096 / 8097 | [`applications/sample-python-worker/`](file:///d:/project/billing-system-master/billing-system-master/applications/sample-python-worker) |
| **`sample-go-service`** | Go 1.27.3 Gin API + Distroless Non-Root | `go` / `dockerfile` | 8101 / 8102 / 8103 | [`applications/sample-go-service/`](file:///d:/project/billing-system-master/billing-system-master/applications/sample-go-service) |

---

## 5. Security & Governance Policies

### 5.1 Non-Root Runtime Policy (A1-SEC-001)
All container images must execute as a non-privileged user:
```dockerfile
# Compliant Distroless Go Dockerfile:
FROM gcr.io/distroless/static-debian12:nonroot
USER nonroot:nonroot
```
*Dockerfiles running as `root` (UID 0) or omitting the `USER` directive will be rejected with Exit Code 20 (`SECURITY_POLICY_VIOLATION`).*

### 5.2 Dependency Lockfile Requirement
Unpinned dependencies are prohibited. Your repository must contain one of:
- Go: `go.sum` or `go.mod`
- Node.js: `package-lock.json` or `yarn.lock`
- Python: `requirements.txt` or `pyproject.toml`
- Java: `pom.xml` or `build.gradle`

### 5.3 Prohibited Runtimes
Outdated or EOL runtimes are rejected at build preflight:
- Prohibited: Node.js <= 18, Python <= 3.9, Java <= 8, Go <= 1.22.

---

## 6. Common Developer Troubleshooting

| Issue / Error | Cause | Remediation |
| :--- | :--- | :--- |
| `Exit Code 10: SPEC_ERROR` | Syntax error or schema violation in `app.spec.yaml`. | Run `python -m platform_core.engine.cli validate --spec <path>` to see exact field errors. |
| `Exit Code 15: CATALOG_ERROR` | Application ID not registered or branch/env unauthorized. | Register via `onboard-app` or update `applications.yaml`. |
| `Exit Code 20: SECURITY_POLICY_VIOLATION` | Root container execution or prohibited runtime version. | Add `USER nonroot:nonroot` or update runtime version in `app.spec.yaml`. |
| `Port Allocation Collision` | Custom port requested is already claimed by another service. | Omit `local_port` to allow the catalog to allocate an isolated port automatically. |
