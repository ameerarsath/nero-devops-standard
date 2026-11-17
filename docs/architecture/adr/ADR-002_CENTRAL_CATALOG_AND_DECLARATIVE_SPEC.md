# Architecture Decision Record: ADR-002
## Title: Central Application Catalog & Declarative Application Specifications

**Status:** Accepted  
**Date:** 2026-11-08  
**Context:**  
Historically, onboarding a new service required writing and maintaining bespoke Jenkinsfiles or deployment scripts for each repository. This led to fragmented practices, security drift, and high maintenance overhead.

**Decision:**  
1. **Central Application Catalog**: The platform maintains an authoritative catalog (`platform_core.engine.catalog`) defining approved application IDs, authorized target environments, permitted platforms (Floci, AWS), and approved account topologies.
2. **Declarative Specification (`app.spec.yaml`)**: Applications describe their architecture declaratively:
   - Metadata (name, version, owner).
   - Components (backend, frontend, worker).
   - Build adapters (`dockerfile`, `node`, `maven`, `python`).
   - Network bindings (internal container ports, health check paths).
   - Dependencies (RDS PostgreSQL, SQS, DynamoDB, S3).
3. **Formal Schema Validation**: Specifications are parsed and validated via Pydantic models before any pipeline action. Unsupported or unauthorized applications fail closed during the preflight stage.

**Consequences:**  
- Positive: Application developers do not write or maintain CI/CD pipelines; onboarding is purely configuration-driven.
- Positive: Standardized health probes, runtime images, and port assignments across all services.
