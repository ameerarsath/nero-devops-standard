# NERO A4 authoritative task register

Updated: 2026-11-16 (Asia/Calcutta). Baseline: `docs/architecture/NERO_A4_IMPLEMENTATION_READINESS_AND_KICKOFF_PLAN.md`, 24 tasks, 188 nominal engineering hours. `DECISION-A4-GATE3-001` records owner authorization for the remaining 21 tasks under `PLAN-A4-PHASES-001` (`NERO-A4-GATE3-20261115-001`). `DRAFT` means planned and unassigned; Gate 3 approval alone does not start a task. Milestone dependencies below are the approved roadmap's coarse dependencies; refine task dependencies before individual assignment.

| Task ID | Milestone | Title | Estimate (EH) | Dependency | Authorization | Lifecycle / acceptance |
|---|---:|---|---:|---|---|---|
| A4-CAN-001 | 1 | Candidate Release Contract Model | 8 | A3 CI evidence | Task-specific historical authorization recorded | ACCEPTED with remediations |
| A4-CAN-002 | 1 | Candidate Ingestion & Preflight Validator | 8 | CAN-001, catalog | Task-specific historical authorization and remediation recorded | ACCEPTED per historical record; remediation reported complete |
| A4-MAN-001 | 1 | Universal Release Manifest v2 Schema | 8 | CAN-001, CAN-002 | Task-specific authorization granted: NERO-A4-MAN-001-TASK-AUTH-20261114-001 | ACCEPTED; evaluation EVALUATION-TASK-A4-MAN-001-003 |
| A4-MAN-002 | 1 | Manifest Serializer & Catalog Registrar | 6 | MAN-001 | Gate 3 authorized: NERO-A4-GATE3-20261115-001 | ACCEPTED; EVALUATION-TASK-A4-MAN-002; Phase 1 accepted |
| A4-REG-001 | 2 | BaseRegistryAdapter Interface | 6 | Milestone 1 accepted | Gate 3 authorized: NERO-A4-GATE3-20261115-001 | ACCEPTED; EVALUATION-A4-PHASE-2-003 |
| A4-REG-002 | 2 | Expanded OCI Distribution Adapter | 10 | REG-001 result, local OCI registry | Gate 3 authorized: NERO-A4-GATE3-20261115-001 | ACCEPTED; EVALUATION-A4-PHASE-2-003; live smoke pending Phase 6 |
| A4-REG-003 | 2 | S3 Static Artifact Release Adapter | 8 | REG-001 result, local Floci S3 | Gate 3 authorized: NERO-A4-GATE3-20261115-001 | ACCEPTED; EVALUATION-A4-PHASE-2-003; live smoke pending Phase 6 |
| A4-REG-004 | 2 | Multi-Component Distribution Dispatcher | 8 | REG-002 and REG-003 results | Gate 3 authorized: NERO-A4-GATE3-20261115-001 | ACCEPTED; EVALUATION-A4-PHASE-2-003; live smoke pending Phase 6 |
| A4-SEC-001 | 3 | Syft SBOM Generation Adapter | 10 | Milestones 1-2 accepted | Gate 3 authorized: NERO-A4-GATE3-20261115-001 | ACCEPTED; EVALUATION-A4-PHASE-3-008; live Syft qualification remains Phase 6 |
| A4-SEC-002 | 3 | In-Toto Build Provenance Attestation | 8 | SEC-001 result | Gate 3 authorized: NERO-A4-GATE3-20261115-001 | ACCEPTED; EVALUATION-A4-PHASE-3-008 |
| A4-SEC-003 | 3 | Cosign Digital Signing Adapter | 10 | SEC-002 result | Gate 3 authorized: NERO-A4-GATE3-20261115-001 | ACCEPTED; EVALUATION-A4-PHASE-3-008; live Cosign qualification remains Phase 6 |
| A4-SEC-004 | 3 | Supply Chain Evidence Aggregator | 6 | SEC-001 through SEC-003 results | Gate 3 authorized: NERO-A4-GATE3-20261115-001 | ACCEPTED; EVALUATION-A4-PHASE-3-008 |
| A4-QLF-001 | 4 | 12-Step Release Qualification Engine | 10 | Milestones 1-3 accepted | Gate 3 authorized: NERO-A4-GATE3-20261115-001; TASK-A4-QLF-001 | ACCEPTED; EVALUATION-A4-PHASE-4-004 |
| A4-QLF-002 | 4 | Release Finite State Machine | 8 | QLF-001 result | Gate 3 authorized: NERO-A4-GATE3-20261115-001; TASK-A4-QLF-002 | ACCEPTED; EVALUATION-A4-PHASE-4-004 |
| A4-QLF-003 | 4 | Release Security Policy Validator | 8 | QLF-002 result | Gate 3 authorized: NERO-A4-GATE3-20261115-001; TASK-A4-QLF-003 | ACCEPTED; EVALUATION-A4-PHASE-4-004 |
| A4-QLF-004 | 4 | Release Audit Ledger Integrator | 6 | QLF-003 result | Gate 3 authorized: NERO-A4-GATE3-20261115-001; TASK-A4-QLF-004 | ACCEPTED; EVALUATION-A4-PHASE-4-004; no authoritative ledger writes |
| A4-PRM-001 | 5 | Zero-Rebuild Promotion Engine | 10 | Milestones 1-4 accepted | Gate 3 authorized: NERO-A4-GATE3-20261115-001; TASK-A4-PRM-001 | ACCEPTED in tested local scope; EVALUATION-A4-PHASE-5-002; live target qualification pending |
| A4-PRM-002 | 5 | Two-Person Production Governance Gate | 10 | PRM-001 result | Gate 3 authorized: NERO-A4-GATE3-20261115-001; TASK-A4-PRM-002 | IMPLEMENTATION_COMPLETED; provisionally verified, Phase 5 acceptance pending |
| A4-PRM-003 | 5 | Release Declarative Jenkinsfile | 8 | PRM-002 result | Gate 3 authorized: NERO-A4-GATE3-20261115-001; TASK-A4-PRM-003 | REMEDIATION_REQUIRED; PRM3-08 exact signature/subject binding in EVALUATION-A4-PHASE-5-004 |
| A4-PRM-004 | 5 | Trusted Shared Library Release Steps | 4 | PRM-003 result | Gate 3 authorized: NERO-A4-GATE3-20261115-001; TASK-A4-PRM-004 | REMEDIATION_REQUIRED; PRM3/4-07 key-policy wiring in EVALUATION-A4-PHASE-5-004 |
| A4-ROL-001 | 6 | Deterministic Rollback Orchestrator | 8 | Milestones 1-5 | Gate 3 authorized; assignment pending | DRAFT |
| A4-RET-001 | 6 | Artifact Lifecycle & Retention Sweeper | 6 | Milestones 1-5 | Gate 3 authorized; assignment pending | DRAFT |
| A4-REV-001 | 6 | Release Revocation Coordinator | 6 | Milestones 1-5 | Gate 3 authorized; assignment pending | DRAFT |
| A4-TST-001 | 6 | End-to-End Release Qualification Suite | 8 | Milestones 1-5, release/rollback paths | Gate 3 authorized; assignment pending | DRAFT |

The later remediation report's `A4-CAN-003` reference conflicts with the approved task 4 `A4-MAN-002`; this register retains the approved baseline. The Gate 3 authorization does not authorize Git commits, pushes, real AWS use, destructive Terraform/Docker operations, or work outside published assignments. Codex updates the register after meaningful task transitions. `INSTRUCTION-A4-PHASE-GATES-001` supersedes the earlier batch review cadence: each phase requires independent Codex acceptance before the next phase is assigned.
