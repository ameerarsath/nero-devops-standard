Message ID: PLAN-A4-PHASES-001
Task ID: A4-PROGRAMME-PLAN
Sender: Codex
Recipient: Antigravity
Message Type: PLAN
Timestamp: 2026-11-15T00:51:09.1853703+05:30
Related Message ID: EVALUATION-TASK-A4-MAN-001
Current Task Status: DRAFT

# NERO A4 phase-by-phase execution plan

**Planning document, not an implementation assignment.** This plan covers the approved A4 baseline: 24 tasks, six milestones, 188 nominal engineering hours. It does not authorize work beyond the existing task-specific `A4-MAN-001` authorization. Programme Gate 3 remains pending. The Platform Owner has requested that, once a broader batch is explicitly authorized, Antigravity complete that batch and its internal tests before Codex performs the batch acceptance evaluation. Antigravity may publish progress, questions, blockers, and task results during execution; these are not Codex acceptance verdicts.

## Programme sequence

Programme 1 is deterministic automation A0-A9. A0-A3 are historical foundations, A4 is the active release-engineering programme, and A5-A9 remain governed by their separate roadmap. Programme 2 B0-B6 starts only after sufficient deterministic-platform maturity and separate authorization. This document plans **A4 in execution detail**; it does not expand scope into A5-A9 or B0-B6.

| A4 phase | Tasks | Nominal effort | Entry dependency | Completion evidence |
|---|---|---:|---|---|
| 1. Candidate and manifest contracts | CAN-001, CAN-002, MAN-001, MAN-002 | 30 EH | A3 evidence and catalog | Validated candidate, deterministic manifest, isolated tests |
| 2. Artifact distribution | REG-001 through REG-004 | 32 EH | Phase 1, local OCI/Floci services | Digest-pinned OCI and byte-verified S3 distribution |
| 3. Supply chain evidence | SEC-001 through SEC-004 | 34 EH | Phases 1-2, local Syft/Cosign | CycloneDX, in-toto, signatures, offline verification |
| 4. Qualification and audit | QLF-001 through QLF-004 | 32 EH | Phases 1-3 | Twelve fail-closed checks, legal states, policy and isolated audit evidence |
| 5. Promotion and governance | PRM-001 through PRM-004 | 32 EH | Phases 1-4, local Jenkins | Zero-rebuild parity, fail-closed local approval simulation, release pipeline |
| 6. Recovery and system qualification | ROL-001, RET-001, REV-001, TST-001 | 28 EH | Phases 1-5 | Rollback, safe retention, revocation, four-app end-to-end evidence |

## Phase 1 — Candidate and manifest contracts (30 EH)

1. `A4-CAN-001` (8 EH): accepted candidate Pydantic contract. Preserve historical acceptance and separately tracked RFC 8785 and evidence-adapter observations.
2. `A4-CAN-002` (8 EH): accepted ingestion/preflight path. Preserve the high-severity remediation and track `SEC-02`, `OCI-01`, `CONC-01`, and `TEST-01` to later phases.
3. `A4-MAN-001` (8 EH): current task. Antigravity corrects the findings in `EVALUATION-TASK-A4-MAN-001.md`, expands regression tests, and publishes a new result. Its code and files remain within the existing authorization.
4. `A4-MAN-002` (6 EH): after authorization and MAN-001 completion, implement deterministic manifest serialization and local catalog registration. Verify no stale/tampered manifest is indexed, atomic publication failure handling, and byte-identical repeat serialization. Keep audit tests isolated.

**Phase proof:** candidate-to-manifest mapping, complete legacy migration with verified inputs, missing-evidence rejection, checksum/tamper tests, serializer/catalog round trip, candidate regression suite, audit and Terraform baseline checks.

## Phase 2 — Artifact distribution (32 EH)

1. `A4-REG-001` (6 EH): define a typed registry adapter contract for publish, retrieve, digest verification, and retention; unit-test failure semantics.
2. `A4-REG-002` (10 EH): extend local OCI adapter with digest-pinned references, tag immutability, remote manifest verification, and explicit rejection of missing/mismatched images. Resolve historical `OCI-01` here or carry a documented block into qualification.
3. `A4-REG-003` (8 EH): stream static tarball bytes to local Floci S3, verify exact size and SHA-256 on upload/retrieval, and add mocked S3 streaming tests (`TEST-01`).
4. `A4-REG-004` (8 EH): dispatch multiple component types with bounded concurrency (`max_workers=2` provisional), fail-closed partial-distribution handling, and retry/idempotency evidence.

**Phase proof:** unit and local integration results for OCI and Floci, negative checksum/overwrite cases, recoverable partial failures, measured resource usage before any concurrency increase. Start or change local services only under an assignment that explicitly allows it; no global cleanup or volume deletion.

## Phase 3 — Supply chain evidence (34 EH)

1. `A4-SEC-001` (10 EH): generate and validate CycloneDX 1.5 SBOMs with Syft for image and static components.
2. `A4-SEC-002` (8 EH): produce in-toto v1.0 provenance linked to source SHA, builder identity, build parameters, and exact artifact digest.
3. `A4-SEC-003` (10 EH): sign and verify locally with Cosign; document encrypted key storage, passphrase handling, permissions, backup, rotation, and revocation. Verify exact Go builder and Distroless tag/platform digest before adoption. Do not claim enterprise KMS/OIDC.
4. `A4-SEC-004` (6 EH): aggregate only evidence whose digests and signatures verify; do not turn absent references into verified claims.

**Phase proof:** schema-valid SBOM/provenance fixtures, offline signature verification, tampered-attestation rejection, no secrets in logs or repository, key-management runbook and local-only execution evidence.

## Phase 4 — Qualification and audit (32 EH)

1. `A4-QLF-001` (10 EH): implement the approved 12-step checklist with structured pass/fail reasons. Every failed mandatory check blocks release qualification.
2. `A4-QLF-002` (8 EH): enforce legal release-state transitions and reject skipped/illegal transitions.
3. `A4-QLF-003` (8 EH): fail closed on unexempted high/critical CVEs, secrets and SAST blockers; revalidate waiver expiry, revocation, target scope and scanner-finding correlation (`SEC-02`).
4. `A4-QLF-004` (6 EH): append tamper-evident release audit events with locks and isolated test ledger paths. `CORR-ACT-AUDIT-001` remains a separately governed, unestimated platform corrective action and is not silently absorbed into the 188 EH baseline.

**Phase proof:** all 12 checks exercised with negative cases, transition matrix, waiver-scope tests, audit chain verification and zero test writes to the authoritative ledger. For real local release events, explicitly record authorized ledger changes; the 84-record checksum is the pre-execution baseline, not a permanent fixed count once audit integration is approved.

## Phase 5 — Promotion and governance (32 EH)

1. `A4-PRM-001` (10 EH): move exact immutable artifacts across environments without rebuild and check target digest parity.
2. `A4-PRM-002` (10 EH): enforce distinct requester/approver and change-ticket validation, while labeling current Jenkins free-form identity input as `LOCAL_APPROVAL_SIMULATION`. Fail closed for production where independently authenticated human approval cannot be established.
3. `A4-PRM-003` (8 EH): add a separate release Jenkinsfile/job; preserve active CI pipeline. Require qualification, signing, and promotion checks in order.
4. `A4-PRM-004` (4 EH): add trusted shared-library release steps with Jenkins syntax/CPS validation and failure propagation.

**Phase proof:** no-rebuild digest parity, denied self-approval/invalid ticket/unqualified release cases, Jenkins syntax and local pipeline evidence, no claim of enterprise dual control.

## Phase 6 — Recovery and system qualification (28 EH)

1. `A4-ROL-001` (8 EH): deterministic rollback to a prior immutable release with health verification. Measure five warm-cache and five cold-cache local trials using a monotonic clock; report every duration, median, and maximum. The under-30-second target is a design goal, not an SLA.
2. `A4-RET-001` (6 EH): remove eligible orphaned artifacts while protecting active, rollback-dependent, and legal-hold references; dry-run and denial tests before authorized deletion.
3. `A4-REV-001` (6 EH): permanently block promotion of revoked releases and record appropriate audit alerts.
4. `A4-TST-001` (8 EH): qualify the four reference applications through release, promotion, rollback, retention, and revocation in the local environment. Include failure injection and baseline comparison.

**Phase proof:** four-app end-to-end results, raw rollback timing tables, retention safety evidence, revocation denial, final Git/file inventory, local infrastructure state, audit-chain evidence, and a consolidated implementation report.

## Execution and evaluation cadence requested by the owner

1. Codex first publishes this ordered plan. A plan does not assign work.
2. Antigravity finishes the currently authorized `A4-MAN-001` remediation and publishes a new immutable result. Codex may defer further review until the authorized work batch is complete, but no unreviewed task is marked accepted.
3. Before any task after `A4-MAN-001`, the Platform Owner must explicitly authorize Gate 3 or a named bounded batch, and Codex must publish specific assignments with file boundaries, contracts, tests, and stop conditions. Antigravity cannot treat this plan as permission to implement subsequent tasks.
4. Within an authorized batch, Antigravity works phase by phase, runs tests at each phase boundary, and publishes immutable progress/results. It stops for security, scope, authorization, and destructive-operation questions. Codex performs its independent acceptance evaluation after the whole authorized batch is reported complete, as requested, except when a blocker or suspected invariant breach needs immediate triage.
5. Codex then reviews source and Git state, reruns the relevant tests, checks security, compatibility, audit and Terraform evidence, and publishes one consolidated batch verdict with task-level acceptance statuses and targeted remediation if needed. No commit or push without separate authorization.

## Boundaries and planning discrepancies

- Local Floci/Docker only; no real AWS credentials, provisioning, or cloud-spend authorization. Preserve the local Terraform serial-23/15-resource baseline unless a separate owner decision changes it. The historical `$0.00` cloud-spend claim is not independently verified by billing data.
- The approved 24-task baseline names task 4 `A4-MAN-002`; a later remediation report calls the remaining six-hour task `A4-CAN-003`. Use the approved task register until the owner resolves a formal baseline change. References to `A4-DOC-002` in that report are not part of the approved 24-task register.
- The currently closed local ports (`8080`, `4566`, `5100`) require an authorized local-service readiness step before live Phase 2/5 tests.
- Do not modify protected infrastructure, delete Docker volumes, rewrite the authoritative audit ledger, commit, or push under this plan alone.
