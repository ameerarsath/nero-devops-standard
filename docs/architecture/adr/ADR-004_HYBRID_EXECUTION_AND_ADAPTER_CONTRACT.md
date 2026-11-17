# Architecture Decision Record: ADR-004
## Title: Hybrid Execution Architecture & Typed Adapter Contracts

**Status:** Accepted  
**Date:** 2026-11-08  
**Context:**  
The platform must support running on developer workstations, local simulation environments (Floci), and production cloud infrastructure (AWS) without altering core orchestration logic.

**Decision:**  
1. **Typed Adapter Contracts**: All platform capabilities are exposed through versioned, abstract Python interfaces:
   - `BaseBuildAdapter` (`dockerfile`, `node`, `maven`, `python`).
   - `BaseInfrastructureAdapter` (`terraform`).
   - `BaseDeploymentAdapter` (`ecs_adapter`, `s3_adapter`).
   - `BaseVerificationAdapter` (`health_verifier`).
2. **Context Resolution**: The `EnvironmentResolver` maps abstract requests `(app_id, env, platform, topology)` into concrete parameters (ports, endpoints, directories, account IDs).
3. **Floci-First Local Simulation**: In the local execution plane, Floci (`http://floci:4566`) provides high-fidelity AWS API emulation (S3, Secrets Manager, DynamoDB, SQS, RDS proxy), while the local Docker daemon acts as the ECS runtime.
4. **Cloud Adapter Parity**: When targeting Real AWS, the same pipeline triggers Terraform targeting AWS ECS Fargate, ALB, S3, and RDS Multi-AZ without changing the Jenkinsfile or application code.

**Consequences:**  
- Positive: Zero cloud costs during local development and testing.
- Positive: Decoupled architecture allowing future Kubernetes or multi-cloud adapters to be added easily.
