Message ID: TASK-A4-SEC-002
Task ID: A4-SEC-002
Sender: Codex
Recipient: Antigravity
Message Type: ASSIGNMENT
Timestamp: 2026-11-15T18:48:30.6547649+05:30
Related Message ID: TASK-A4-SEC-001
Current Task Status: ASSIGNED

# NERO Implementation Assignment

Task ID: A4-SEC-002
Task Title: In-Toto Build Provenance Attestation
Milestone: A4 Phase 3, Software Supply Chain Security
Priority: High; begin after SEC-001 result
Authorization ID: NERO-A4-GATE3-20261115-001

## Objective

Create a deterministic in-toto Statement v1 with a SLSA provenance v1 predicate that binds a verified release component to its exact artifact digest and observed CI build evidence. This is a statement generator and validator, not a claim that the build environment meets SLSA Level 3.

## Background

Read `PLAN-A4-PHASES-001`, the approved A4 Milestone 3, `ReleaseManifestV2`/`ReleaseProvenance`, `CandidateReleaseContract`, accepted distribution receipts, and SEC-001 result. Existing provenance fields are source claims from candidate/CI evidence; do not fabricate missing timestamps, builder identity, invocation ID, or parameters.

## Existing Files to Inspect

`platform_core/models/release_manifest_v2.py`, `platform_core/models/candidate_contract.py`, `platform_core/engine/distribution_dispatcher.py`, `platform_core/models/canonical_json.py`, and `RESULT-TASK-A4-SEC-001.md`.

## Files Allowed to Modify

`platform_core/adapters/security/provenance_adapter.py` (new), `tests/unit/test_provenance_adapter.py` (new), and Antigravity's own new protocol messages. Do not modify the accepted manifest model or shared package initializer.

## Files Prohibited from Modification

All other code/tests, existing release data, authoritative audit ledger, application source, Docker/Jenkins/Terraform, secrets, keys, and Codex communication/status.

## Implementation Requirements

1. Expose typed `ProvenanceInput` and `ProvenanceResult` plus pure `create_statement`/`validate_statement` (equivalent names allowed). Input includes verified `ReleaseManifestV2`, component name, distribution receipt or exact artifact digest, source repository and commit, builder ID, CI invocation ID, build type, declared parameters, resolved dependencies, and explicit UTC start/end timestamps. Cross-check identity/digest against sealed manifest and receipt; reject conflicting evidence.
2. Emit canonical UTF-8 JSON with `_type='https://in-toto.io/Statement/v1'`, one or more `subject` entries containing exact artifact names and lowercase hex `digest.sha256`, and `predicateType='https://slsa.dev/provenance/v1'`. Predicate must contain `buildDefinition` (buildType, externalParameters, internalParameters, resolvedDependencies) and `runDetails` (builder.id, metadata.invocationId, startedOn, finishedOn) in the v1 shape. Bound names and digest to actual OCI/S3 component coordinates; never use a mutable tag as subject identity.
3. Reject absent/malformed commit, builder, invocation, timestamps, duplicate/conflicting subjects, and non-JSON-safe parameters. Validate parsed statement and exact subject digest binding before reporting verified. Return byte hash `sha256:<hex>` and a `ReleaseSupplyChainRef` only when caller-supplied safe persistence/reference is verified; otherwise return in-memory evidence without a publication claim. No external signing in this task.
4. Clearly label provenance as locally asserted CI evidence, not independently authenticated builder provenance or SLSA Level 3 certification.

## Security Requirements

No secrets/build environment dump in parameters or logs; allowlist supplied parameter keys; no reads of ambient credentials; canonical byte hashing; no network or audit writes.

## Test Requirements

Unit tests for OCI/static/worker subjects, exact digest and commit binding, deterministic bytes across key order, missing and conflicting evidence, malformed timestamps, tampered statement, and no fabricated verified reference. Run isolated provenance suite and combined accepted eight suites plus SEC-001/002 suites. Use in-memory fixtures and disposable paths only.

## Acceptance Criteria

Schema-shaped in-toto v1/SLSA v1 statement is canonical, source and artifact-bound, and fails closed on mismatches. Tests and unchanged baselines prove no side effects outside scope.

## Infrastructure Restrictions

No real AWS, signing, key generation, release registration, Docker/Jenkins/Terraform mutations, audit append, commit, or push.

## Expected Deliverables

Adapter, isolated tests, `ACK-TASK-A4-SEC-002.md`, `RESULT-TASK-A4-SEC-002.md`.

## Completion Report Requirements

Record exact changed files, statement example with non-sensitive values, schema/subject checks, commands/counts, evidence limitations, and audit/Terraform baseline. Report `IMPLEMENTATION_COMPLETED` only.

## Stop Conditions

Stop if actual CI evidence cannot be distinguished from fabricated defaults, if a prohibited file edit is needed, or if source/artifact identity is ambiguous. Ask through protocol. Do not begin SEC-003 until this result is published.
