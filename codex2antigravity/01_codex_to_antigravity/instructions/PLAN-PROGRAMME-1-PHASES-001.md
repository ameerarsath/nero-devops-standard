Message ID: PLAN-PROGRAMME-1-PHASES-001
Task ID: PROGRAMME-1-ROADMAP
Sender: Codex
Recipient: Antigravity
Message Type: PLAN
Timestamp: 2026-11-17T16:50:15.1966587+05:30
Related Message ID: PLAN-A4-PHASES-001
Current Task Status: DRAFT

# NERO Programme 1: complete phase map (A0–A9)

**Planning map only; this is not an implementation assignment or authorization.** Programme 1 is deterministic automation. Programme 2 (B0–B6) remains separate. The authoritative A4 24-task, 188-EH baseline and individual `TASK-*.md` assignments remain controlling. A5–A9 work packages below are provisional planning units, not registered task IDs or estimates.

## Operating sequence

1. Plan the programme and each phase before starting dependent implementation. Preserve this plan as an immutable message; issue a new numbered revision to change it.
2. For each active phase, Codex refines task contracts, file boundaries, dependencies, test matrix, and stop conditions; publishes specific assignments only within owner authorization.
3. Antigravity acknowledges each assignment, implements in dependency order, runs its tests, and publishes immutable results. A plan never opens an implementation inbox by itself.
4. Codex independently reviews source and tests, checks protected baselines and security claims, and publishes an acceptance or scoped remediation verdict. The next phase is assigned only after the prior phase passes its gate.
5. Maintain `CURRENT_STATUS.md` and `TASK_REGISTER.md` after meaningful transitions. No commit, push, real AWS provisioning, destructive Terraform/Docker operation, authoritative ledger rewrite, or live production promotion is authorized by this plan.

## Programme gates and current position

| Stage | Position | Next gate |
|---|---|---|
| A0–A2 | Historical foundations documented in repository; no new implementation assigned here | Preserve evidence; audit any unresolved exception when a dependent phase needs it |
| A3 | Owner-approved `A3_CLOSURE_VERIFIED_WITH_EXCEPTIONS` | Carry webhook and audit-isolation exceptions truthfully |
| A4 | Gate 3 authorized by `DECISION-A4-GATE3-001`; Phases 1–4 accepted, Phase 5 in PRM-003/004 remediation, Phase 6 unassigned | Accept Phase 5 independently, then assign Phase 6 |
| A5–A9 | Roadmap-defined, detailed task contracts and owner authorization not yet established | Architecture/readiness and owner decision for each stage before assignment |

## A0 — Requirements and architecture freeze (historical)

| Subphase | Work package | Exit evidence |
|---|---|---|
| A0-P1 | Product requirements, supported app types, local-only threat boundary | Approved requirements and scope |
| A0-P2 | Architecture, adapter contracts, ADR-001–005, threat model | Reviewed interface and security decisions |
| A0-P3 | Non-AI A0–A9 and AI B0–B6 roadmaps, governance baseline | Frozen roadmap with explicit decision owners |

Treat A0 as a historical evidence baseline. Do not recreate or overwrite existing decisions.

## A1 — Local platform foundation and Floci qualification (historical)

| Subphase | Work package | Exit evidence |
|---|---|---|
| A1-P1 | Isolated local Docker/Floci/Jenkins/registry topology and credential boundary | Local endpoints and zero-real-cloud configuration |
| A1-P2 | Terraform environment isolation and state protection | Local state integrity, environment separation, non-destructive plan evidence |
| A1-P3 | Local service and failure qualification | Reproducible readiness checks and recovery evidence |

Preserve current Terraform serial 23 and 15 managed resources unless a later owner decision explicitly changes the baseline.

## A2 — Declarative application onboarding (historical)

| Subphase | Work package | Exit evidence |
|---|---|---|
| A2-P1 | `app.spec.yaml` schema and multi-component contracts | Positive/negative schema tests |
| A2-P2 | Central catalog registration and compatibility checks | Catalog identity and dependency validation |
| A2-P3 | Four reference-app onboarding | App-by-app evidence without per-app pipeline forks |

## A3 — Complete CI automation (owner-closed with exceptions)

| Subphase | Work package | Exit evidence |
|---|---|---|
| A3-P1 | SCM adapters, authenticated webhook gateway, trigger idempotency | Provider and replay tests; external SaaS ingress level disclosed |
| A3-P2 | Multi-component build, cache, trusted Jenkins CI library | Deterministic build and cache evidence |
| A3-P3 | Polyglot test, coverage and regression gates | JUnit/coverage/negative-failure evidence |
| A3-P4 | Security scanning, CI evidence, closure audit | Scanner policy and chain evidence; accepted exceptions tracked |

Gate 1 is `A3_CLOSURE_VERIFIED_WITH_EXCEPTIONS`; do not silently upgrade the accepted local qualification to external SaaS certification. Track `CORR-ACT-AUDIT-001` separately.

## A4 — Immutable releases (approved six-phase, 24-task baseline)

The detailed technical plan is `PLAN-A4-PHASES-001.md`. This map preserves its task IDs, estimates, dependencies, and acceptance gates.

| Subphase | Approved tasks | Exit evidence | Current state |
|---|---|---|---|
| A4-P1 Candidate and manifest contracts | CAN-001/002, MAN-001/002 | Candidate-to-manifest identity, checksum, catalog round trip | Accepted |
| A4-P2 Artifact distribution | REG-001–004 | Pinned OCI and byte-verified S3 receipts, fail-closed dispatch | Accepted in tested local/mock scope; live smoke deferred |
| A4-P3 Supply-chain evidence | SEC-001–004 | CycloneDX, in-toto, Cosign, durable subject binding | Accepted in tested scope; live tool qualification deferred |
| A4-P4 Qualification and audit | QLF-001–004 | Twelve checks, FSM, security policy, isolated audit append | Accepted in tested scope |
| A4-P5 Promotion and governance | PRM-001–004 | Zero-rebuild parity, truthful approval boundary, release pipeline | PRM-001 accepted locally; PRM-002 provisional; PRM-003/004 remediation required under `EVALUATION-A4-PHASE-5-004` |
| A4-P6 Recovery and system qualification | ROL-001, RET-001, REV-001, TST-001 | Rollback, retention, revocation, four-app local end-to-end evidence | DRAFT; not assigned |

**Immediate execution order:** resolve PRM-003/004 signature-subject and pipeline key-policy findings; Codex evaluates Phase 5; only on acceptance does Codex assign A4-P6 tasks in dependency order. A4-P6 must expose live Syft/Cosign/OCI/Floci/Jenkins qualification limits and preserve the authoritative audit baseline unless separately authorized to append real events.

## A5 — Infrastructure lifecycle automation (future; provisional)

| Subphase | Work package | Exit evidence |
|---|---|---|
| A5-P1 | Derive environment requirements from validated app specs; design Terraform module contracts for VPC, ECS, S3, RDS, DynamoDB, SQS | Spec-to-plan traceability and no hidden real-cloud defaults |
| A5-P2 | Implement isolated reusable modules and structured `tfplan.<env>` / `infra-outputs.<env>.json` contracts | Module validation and plan determinism in local fixtures |
| A5-P3 | Add pre-apply policy scanning and drift detection | Negative policy tests, read-only drift reports, state safety |
| A5-P4 | Qualify local execution and publish infrastructure acceptance pack | Environment isolation, rollback plan, baseline comparison |

No `terraform apply` against real AWS or real cloud credentials under this plan. Detailed module tasks, estimates, and any state change need their own design and owner authorization.

## A6 — Universal deployment and promotion (future; provisional)

| Subphase | Work package | Exit evidence |
|---|---|---|
| A6-P1 | Specify typed ECS/container and S3/static target adapter interfaces, identity and digest contracts | No-rebuild target contract and failure semantics |
| A6-P2 | Implement local deployment dispatch and automatic port-conflict handling | Exact digest/byte parity and bounded retries |
| A6-P3 | Integrate sequential develop → qa → production state and authorization checks | Denied skip/backward/self-promotion cases; production remains restricted without real governance proof |
| A6-P4 | Qualify health-gated rollback and target recovery | Measured rollback trials and no data loss |

A4 promotion scaffolding is an input, not evidence that A6 live target deployment is complete.

## A7 — Testing and DevSecOps automation (future; provisional)

| Subphase | Work package | Exit evidence |
|---|---|---|
| A7-P1 | Define seven synthetic health probes and environment-specific test contracts | Positive/negative probes and failure diagnosis |
| A7-P2 | Integrate vulnerability scan gates and exact finding/waiver correlation | High/critical, secret and SAST blockers fail closed |
| A7-P3 | Enforce signed image and attestation verification at deployment | Pinned digest and trusted-key evidence, tamper rejection |
| A7-P4 | Four-app environment qualification | All seven probes per applicable target plus scanner evidence |

Reuse A3 scanners and A4 signing components; do not duplicate engines without a documented gap.

## A8 — Observability, recovery and operations (future; provisional)

| Subphase | Work package | Exit evidence |
|---|---|---|
| A8-P1 | Correlation IDs and structured log/metric contracts | Cross-component traceability without secret leakage |
| A8-P2 | Local monitoring for container, port and database failures | Alert thresholds and injected-failure detection |
| A8-P3 | Bounded restart, stale-port cleanup and database retry (25 attempts with backoff) | Idempotency, exhaustion and data-safety tests |
| A8-P4 | Operational runbooks and recovery drills | Measured incident timelines and manual stop controls |

No global Docker cleanup, volume deletion, or destructive restart is authorized by this plan.

## A9 — Enterprise qualification and governance (future; provisional)

| Subphase | Work package | Exit evidence |
|---|---|---|
| A9-P1 | Specify independently authenticated QA Lead/SRE Lead approval and `CHG-*` ticket verification | Separation-of-duties threat tests and identity source decision |
| A9-P2 | Integrate cryptographic audit chain and protected storage/retention policy | Tamper detection, append provenance, access control |
| A9-P3 | End-to-end polyglot and multi-environment qualification | Four-app test matrix, deployment and recovery evidence |
| A9-P4 | Owner acceptance, exception disposition and operational handoff | Signed decision record, residual limitations and runbooks |

Current A4 local two-person simulation cannot be represented as A9 independently authenticated approval. A9 closure requires evidence from the actual approved identity and ticket systems; if unavailable, record an exception rather than a success claim.

## Evidence and authorization boundaries

- Source hierarchy: `docs/architecture/NON_AI_ROADMAP_A0_A9.md`; `docs/architecture/NERO_OWNER_DECISION_001.md`; `DECISION-A4-GATE3-001.md`; `PLAN-A4-PHASES-001.md`; `CURRENT_STATUS.md`; `TASK_REGISTER.md`.
- A4 Gate 3 authorization covers the approved A4 tasks only, with individual assignments. It does not authorize A5–A9, real AWS, production deployment, Git publication, or destructive changes.
- A5–A9 subphase labels are planning handles only. Codex will convert them into specific task IDs, estimates, dependencies, file boundaries and acceptance criteria after architecture/readiness review and the relevant owner decision.
- The authoritative audit ledger baseline is 84 records at SHA-256 `77072d885be691c71a30514be97666a7937deb0aa87ac6f52f5490733c1ddf83`; local Terraform baseline is serial 23/15 resources. Baselines are checked at each gate and changed only through explicit authorized events.
