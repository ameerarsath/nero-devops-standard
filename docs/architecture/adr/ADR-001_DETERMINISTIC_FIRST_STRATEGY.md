# Architecture Decision Record: ADR-001
## Title: Deterministic DevOps Automation Before AI Intelligence

**Status:** Accepted  
**Date:** 2026-11-08  
**Context:**  
Enterprise software delivery requires high reliability, reproducible builds, fail-closed security policies, and deterministic recovery. Introducing large language models (LLMs) or autonomous AI agents as primary orchestrators for critical CI/CD steps creates non-deterministic failure modes, prompt injection risks, and unverified authority.

**Decision:**  
We adopt a strict Two-Programme Strategy:
1. **Programme 1 (Deterministic DevOps Automation)**: All core continuous delivery pipelines, catalog validations, Terraform executions, container deployments, and health verifications are driven 100% by deterministic code, schemas, and Jenkins declarative pipelines. Zero AI dependency is permitted in Programme 1.
2. **Programme 2 (AI-Enhanced DevOps)**: AI capabilities are introduced only after Programme 1 reaches operational maturity. AI operates strictly as an additive intelligence layer (Copilot, Root-Cause Diagnostics, Risk Scoring), adhering to defined Autonomy Tiers (Levels 1 to 5). AI is prohibited from bypassing deterministic policies, secret stores, or human governance approvals.

**Consequences:**  
- Positive: Predictable, auditable, and testable delivery platform; zero non-deterministic deployment failures.
- Positive: Clear regulatory and compliance alignment.
- Consideration: Advanced autonomous self-healing is deferred to Phase B5 after baseline telemetry is fully established.
