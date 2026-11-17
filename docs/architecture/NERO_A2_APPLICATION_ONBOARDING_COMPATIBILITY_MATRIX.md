# NERO Universal Enterprise DevOps Automation Platform
## Application Onboarding Compatibility Matrix
### Technology, Framework, Runtime, and Adapter Support Baseline

**Document Type:** Technical Reference & Compatibility Standard  
**Document ID:** NERO-A2-MATRIX-001  
**Programme:** NERO Programme 1 — Deterministic DevOps Automation  
**Phase:** Phase A2 (Universal Application Onboarding & Catalog Expansion)  
**Security Classification:** Enterprise Internal / Developer Reference  
**Effective Date:** 2026-11-08  
**Author:** NERO Lead DevOps Automation Architect  

---

## 1. Overview & Classification Legend

This document defines the authoritative compatibility and qualification status for programming languages, application frameworks, runtime environments, build adapters, and deployment targets supported by the NERO Enterprise DevOps Automation Platform.

### Support Status Legend

| Status | Code | Definition | Platform Readiness |
|---|---|---|---|
| **Operationally Qualified** | `QUALIFIED` | Fully implemented, hardened, and verified with passing automated test suites in Phase A1. | Production Ready on Floci & Local |
| **Partially Supported** | `PARTIAL` | Can run via generic Dockerfile adapters, but lacks native CLI tooling or fine-grained verification. | Usable with Dockerfile fallback |
| **Proposed for A2** | `PROPOSED_A2` | Architectural design completed; targeted for formal implementation and qualification in Phase A2. | Planned in Phase A2 Backlog |
| **Future Capability** | `FUTURE_A3_A4` | Architectural design acknowledged; deferred to Phase A3 (CI) or Phase A4 (Artifacts & Packaging). | Roadmap (Not in A2) |
| **Unsupported** | `UNSUPPORTED` | Does not align with NERO architectural patterns, stateless container standards, or security policies. | Blocked at Preflight Gate |

---

## 2. Comprehensive Technology & Framework Compatibility Matrix

| Category | Technology / Language | Framework / Tool | Runtime Version | Build Adapter | Deployment Adapter | Support Status | Qualification Requirements |
|---|---|---|---|---|---|---|---|
| **Backend API** | Java | Spring Boot 3.x | OpenJDK 17, 21 | `dockerfile`, `java-maven` | `ecs` | `QUALIFIED` | Non-root `USER`, `/actuator/health` HTTP 200, Flyway DB migration |
| **Backend API** | Java | Quarkus | GraalVM / OpenJDK 21 | `dockerfile` | `ecs` | `FUTURE_A3_A4` | Native image compile, fast startup (<500ms), `/q/health` probe |
| **Backend API** | Node.js | Express | Node 20, 22 LTS | `dockerfile`, `node` | `ecs` | `QUALIFIED` | Non-root `USER`, `/health` HTTP 200, `package-lock.json` |
| **Backend API** | Node.js | NestJS | Node 20, 22 LTS | `dockerfile`, `node` | `ecs` | `PARTIAL` | TypeScript build step, dist bundle validation, `/health` probe |
| **Backend API** | Node.js | Next.js (SSR) | Node 20, 22 LTS | `dockerfile` | `ecs` | `FUTURE_A3_A4` | Standalone output mode, Node server runtime, dynamic routing |
| **Frontend Web** | TypeScript / JS | React (Vite) | Node 20, 22 LTS | `node` | `s3-static` | `QUALIFIED` | SPA deep-link routing, tarball checksum, asset MIME validation |
| **Frontend Web** | TypeScript / JS | React (CRA / Webpack) | Node 20 LTS | `node` | `s3-static` | `PARTIAL` | Build output in `build/` directory, static asset hashing |
| **Frontend Web** | TypeScript / JS | Vue 3 / Vite | Node 20, 22 LTS | `node` | `s3-static` | `PROPOSED_A2` | Vite dist output, SPA routing, index.html verification |
| **Frontend Web** | TypeScript / JS | Angular | Node 20 LTS | `node` | `s3-static` | `PROPOSED_A2` | Multi-directory dist resolution, base-href configuration |
| **Frontend Web** | TypeScript / JS | Svelte / SvelteKit | Node 20, 22 LTS | `node` | `s3-static` | `FUTURE_A3_A4` | Static adapter export, zero SSR dependency |
| **Backend API** | Python | FastAPI / Uvicorn | Python 3.11, 3.12 | `dockerfile`, `python` | `ecs` | `QUALIFIED` | Non-root `USER`, `/health` HTTP 200, strict `requirements.txt` |
| **Backend API** | Python | Flask | Python 3.11, 3.12 | `dockerfile`, `python` | `ecs` | `PARTIAL` | WSGI container (Gunicorn), `/health` endpoint, non-root user |
| **Backend API** | Python | Django | Python 3.11, 3.12 | `dockerfile` | `ecs` | `FUTURE_A3_A4` | Collectstatic stage, DB migrations, Gunicorn/Uvicorn |
| **Backend API** | Go | Standard `net/http` | Go 1.21, 1.22 | `dockerfile`, `go` | `ecs` | `PROPOSED_A2` | CGO_ENABLED=0, Distroless/Scratch, `/health` HTTP 200 |
| **Backend API** | Go | Gin / Fiber | Go 1.21, 1.22 | `dockerfile`, `go` | `ecs` | `PROPOSED_A2` | Multi-stage Dockerfile, `/health` endpoint, non-root UID 10001 |
| **Worker** | Python | Thread Queue / SQS | Python 3.12 | `dockerfile` | `ecs` (or `ecs-worker`) | `QUALIFIED` | Daemon thread lifecycle, graceful SIGTERM, SQS polling |
| **Worker** | Python | Celery + Redis | Python 3.11, 3.12 | `dockerfile` | `ecs-worker` | `FUTURE_A3_A4` | Redis broker dependency, task health probe, concurrency tuning |
| **Worker** | Go | SQS Channel Worker | Go 1.22 | `dockerfile`, `go` | `ecs-worker` | `PROPOSED_A2` | Goroutine pool, AWS SDK v2 SQS consumer, graceful shutdown |
| **Database** | Relational | PostgreSQL 15, 16 | Floci / Localhost:5432 | Terraform Module | RDS Module | `QUALIFIED` | Schema isolation, automated credentials via Secrets Manager |
| **Database** | NoSQL | DynamoDB | Floci DynamoDB Mock | Terraform Module | Dynamo Module | `QUALIFIED` | Hash key specification, billing mode PAY_PER_REQUEST |
| **Database** | Key-Value / Cache | Redis 7.x | Localhost:6379 | Terraform Module | ElastiCache | `FUTURE_A3_A4` | Standalone cache cluster, auth token in Secrets Manager |
| **Database** | Document | MongoDB | N/A | Unsupported | Unsupported | `UNSUPPORTED` | Non-relational external database outside AWS managed scope |
| **Custom OCI** | Polyglot | Multi-stage Dockerfile | Custom | `dockerfile` | `ecs` | `QUALIFIED` | Explicit non-root `USER`, zero secrets in layers, port mapping |

---

## 3. Build & Deployment Adapter Specifications

### 3.1 Build Adapters

| Adapter Name | Interface Class | Primary Inputs | Produced Outputs | Security Policies Enforced |
|---|---|---|---|---|
| **`dockerfile`** | `DockerfileBuildAdapter` | `Dockerfile`, build context, build args | OCI Image Tag, SHA-256 Digest | AST Non-root linter (`USER <uid>`), layer cache hygiene, zero embedded secrets |
| **`node`** | `NodeFrontendBuildAdapter` | `package.json`, `dist_dir`, build cmd | Static Dist Directory, Tarball, SHA-256 | Lockfile enforcement (`package-lock.json`), safe tarball containment, clean MIME |
| **`java-maven`** *(Proposed A2)* | `JavaMavenBuildAdapter` | `pom.xml`, source code | JAR artifact, OCI container image | Approved Maven plugins, target JDK validation, hermetic build |
| **`python`** *(Proposed A2)* | `PythonBuildAdapter` | `pyproject.toml` / `requirements.txt` | Wheel, Virtualenv, OCI image | Pinned dependency versions, hash checking, non-root user |
| **`go`** *(Proposed A2)* | `GoBuildAdapter` | `go.mod`, `go.sum`, source | Static binary, Distroless OCI image | `CGO_ENABLED=0`, stripped debug symbols (`-s -w`), vulnerability audit |

### 3.2 Deployment Adapters

| Adapter Name | Interface Class | Target Infrastructure | Deployment Strategy | Health Verification |
|---|---|---|---|---|
| **`ecs`** | `ECSDeploymentAdapter` | Floci ECS Simulation / AWS ECS Fargate | Zero-downtime rolling container replacement | Strict HTTP 200 on health path, automatic port conflict self-healing |
| **`s3-static`** | `S3FrontendDeploymentAdapter` | Floci S3 Simulator / AWS S3 + CloudFront | Atomic directory synchronization & cache invalidation | HTTP 200 on `index.html`, static JS/CSS asset probe, SPA routing fallback |
| **`ecs-worker`** *(Proposed A2)* | `ECSWorkerDeploymentAdapter` | Floci ECS Simulation / AWS ECS Fargate | Daemon / Headless worker container | Process heartbeat / worker health socket, queue depth monitoring |

---

## 4. Health Probe Protocols & Status Classifications

To ensure deterministic reliability, the platform strictly enforces standardized status classifications during synthetic verification:

| Check Type | Target Endpoint | Expected Status | Strict Pass Criteria | Platform Failure Action |
|---|---|---|---|---|
| **Backend Container Health** | `http://<host>:<port><health_path>` | `HTTP 200 OK` | ONLY `HTTP 200` is accepted. `HTTP 401`, `403`, `500` strictly rejected. | Halt pipeline; trigger automatic zero-rebuild rollback. |
| **Frontend Root Entrypoint** | `http://<s3_endpoint>/<bucket>/index.html` | `HTTP 200 OK` | Valid HTML document with `<!DOCTYPE html>`. | Halt pipeline; fail deployment. |
| **Frontend Static Assets** | `http://<s3_endpoint>/<bucket>/assets/*.js` | `HTTP 200 OK` | Valid `Content-Type: application/javascript` or `text/css`. | Warning / Halt if critical bundle missing. |
| **SPA Deep-Link Routing** | `http://<s3_endpoint>/<bucket>/<route>` | `HTTP 200 OK` (AWS) / `404` (Floci) | On AWS, CloudFront rewrites 404 to `/index.html` with HTTP 200. On Floci, classified as `EXPECTED_PLATFORM_LIMITATION`. | Pass on Floci; Strict HTTP 200 on AWS. |
| **Negative Missing Asset** | `http://<s3_endpoint>/<bucket>/missing-probe.js` | `HTTP 404 Not Found` | Strictly asserts 404 response to verify error boundary integrity. | Halt if missing probe returns 200 or 500. |

---

## 5. Technology Qualification Requirements for Phase A2

Every application seeking onboarding certification in Phase A2 must satisfy the following technical prerequisites:

### 5.1 Node.js Services (`sample-node-service`)
- [x] Defined in `applications/sample-node-service/app.spec.yaml`.
- [x] Must contain a valid `package-lock.json`.
- [x] Must expose a health check endpoint at `/health` returning `{"status": "UP"}`.
- [x] Must include non-root `USER node` directive in its `Dockerfile`.
- [x] Verified operational on local Floci port `8091` (develop), `8092` (qa), `8093` (prod).

### 5.2 Python Workers (`sample-python-worker`)
- [x] Defined in `applications/sample-python-worker/app.spec.yaml`.
- [x] Must contain pinned dependencies in `requirements.txt`.
- [x] Must expose an HTTP health probe on `PORT` (default `8000`) returning HTTP 200.
- [x] Must execute as non-root `USER appuser` (UID 10001).
- [x] Must handle graceful shutdown upon receiving `SIGTERM`.
- [x] Verified operational on local Floci port `8095` (develop), `8096` (qa), `8097` (prod).

### 5.3 Go Microservices (`sample-go-service` - Reference Specification)
- [ ] Defined via standard `app.spec.yaml` v2 schema.
- [ ] Must contain `go.mod` and `go.sum` with valid Go module path.
- [ ] Must compile statically (`CGO_ENABLED=0`).
- [ ] Must package in a minimal Distroless or Alpine container running as non-root (`USER 10001:10001`).
- [ ] Must expose an HTTP health probe at `/health` returning `{"status": "UP"}`.
- [ ] Must allocate unique local simulation ports (e.g. `8101` develop, `8102` qa, `8103` prod).

### 5.4 Hotel Billing Multi-Tier Workload (`hotel-billing` - Regression Standard)
- [x] Multi-tier composition: Spring Boot Java 17 backend + React 19 Vite frontend.
- [x] PostgreSQL relational database dependency with Flyway schema migration.
- [x] Backend verified on Floci ports `8085` (develop), `8087` (qa), `8089` (prod).
- [x] Frontend verified on Floci S3 buckets (`hotel-billing-*-frontend`).
- [x] Serves as mandatory 100% regression gate before any A2 code promotion.
