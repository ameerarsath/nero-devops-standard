Message ID: TASK-A4-PRM-003
Task ID: A4-PRM-003
Sender: Codex
Recipient: Antigravity
Message Type: ASSIGNMENT
Timestamp: 2026-11-17T12:26:30.8559230+05:30
Related Message ID: TASK-A4-PRM-002
Current Task Status: ASSIGNED

# NERO Implementation Assignment

Task ID: A4-PRM-003
Task Title: Release Declarative Jenkinsfile
Milestone: A4 Phase 5, promotion and governance
Priority: High; start after PRM-002 result
Authorization ID: NERO-A4-GATE3-20261115-001

## Objective

Add a separate local release pipeline that consumes the existing candidate/manifest, qualification, security, and promotion contracts in order. Preserve the active CI and deployment pipelines.

## Background

Read the A4 release architecture, `PLAN-A4-PHASES-001`, PRM-001/002 results, current A3 CI Jenkinsfile, universal and production Jenkinsfiles, existing shared library, and Jenkins configuration. PRM-004 supplies the final trusted library wrapper; this task establishes the pipeline and a real fail-closed Python bridge where existing modules have no CLI.

## Existing Files to Inspect

`ci-cd/jenkins/pipelines/ci/Jenkinsfile.ci`, `ci-cd/jenkins/pipelines/universal/Jenkinsfile`, `ci-cd/jenkins/shared-library/vars/neroCI.groovy`, `platform_core/engine/cli.py`, Phase 1-4 module APIs, and PRM-001/002 code.

## Files Allowed to Modify

`ci-cd/jenkins/pipelines/release/Jenkinsfile.release` (new), `platform_core/engine/release_cli.py` (new, if needed for actual module invocation), `tests/unit/test_release_cli.py` (new), and `tests/unit/test_release_jenkinsfile.py` (new), plus Antigravity's acknowledgement/result messages. No edits to existing CI, universal, production, or Jenkins configuration files.

## Files Prohibited from Modification

All other source/tests, existing Jenkinsfiles/shared library, Docker/Terraform, application code, catalogs, authoritative audit ledger, and Codex messages/status.

## Implementation Requirements

Pipeline stages must be ordered: parameter/catalog preflight; candidate and registered manifest validation; distribution and immutable digest evidence verification; supply-chain evidence verification; twelve-step qualification and security policy decision; release registration/audit prerequisites; environment promotion with exact target parity; result reporting. Bind a single app/release/checksum across stages. Use a separate `Jenkinsfile.release`, fixed trusted library revision/configuration, and bounded parameters; reject `aws` or nonlocal endpoints and unknown app/environment/action values. Production path must obtain independently authenticated Jenkins principal evidence and PRM-002 ticket decision; local free-form input is labeled simulation and must fail production promotion. QA dry-run must be available without mutating live services. If modules lack command entry points, implement `python -m platform_core.engine.release_cli` subcommands using typed JSON input/evidence files to invoke real functions; parse and validate files within an explicit workspace root, return nonzero for missing/invalid evidence, and never print secrets. A stage must not be a placeholder, hardcoded PASS, or unimplemented success. PRM-004 may later replace direct invocations with trusted library calls without changing security order. If required cross-module contracts are absent, ask a Markdown question instead of fabricating evidence.

## Security Requirements

No build/recompile stage in release pipeline; no arbitrary shell interpolation of user values, unrestricted paths, mutable tags, credential echo, or real AWS. Use Jenkins credentials binding only for approved local secrets; default to read-only/plan execution. Lock the release identity and prevent concurrent conflicting promotions. Preserve test fixtures and authoritative ledger.

## Test Requirements

Test parameter rejection, stage order, missing candidate/manifest/security/qualification evidence, nonzero command propagation, no-build invariant, bad digest/endpoint/production approval, and safe local dry-run. Validate Groovy Declarative syntax with an available local parser/Jenkins if possible; report precisely if unavailable. Run isolated CLI/pipeline tests and full platform regression. Do not mark live integration passed from static tests.

## Acceptance Criteria

The separate pipeline has executable, fail-closed stage calls bound to one immutable release; QA dry-run proves order without live mutation; production lacks a bypass around PRM-002; existing CI files remain byte-identical. A static-only pipeline is not a live Jenkins acceptance claim.

## Infrastructure Restrictions

Read-only local Jenkins inspection/syntax validation is allowed. Do not create/change Jenkins jobs, run a live deploy, edit Docker/Terraform, append authoritative ledger, use real AWS, commit, or push. Request scoped authorization via protocol if a local live qualification step is necessary.

## Expected Deliverables

Allowed new files, `ACK-TASK-A4-PRM-003.md`, `RESULT-TASK-A4-PRM-003.md`.

## Completion Report Requirements

List actual invocations, tests and Jenkins validation performed, changed files, security gates, missing live evidence, and protected baselines.

## Stop Conditions

Start only after PRM-002 result. Stop and ask if a working stage needs a prohibited edit or cannot prove its inputs. Publish result before PRM-004; Phase 6 remains unassigned.
