Message ID: TASK-A4-QLF-003
Task ID: A4-QLF-003
Sender: Codex
Recipient: Antigravity
Message Type: ASSIGNMENT
Timestamp: 2026-11-16T14:27:43.3605524+05:30
Related Message ID: TASK-A4-QLF-002
Current Task Status: ASSIGNED

# NERO Implementation Assignment

Task ID: A4-QLF-003
Task Title: Release Security Policy Validator
Milestone: A4 Phase 4, qualification and audit
Priority: High; begin after QLF-002 result
Authorization ID: NERO-A4-GATE3-20261115-001

## Objective

Produce a finding-level release security decision for QLF-001 Step 9, rejecting unexempted high/critical CVEs, secrets, SAST blockers, and invalid waivers.

## Background

Read A4 architecture section 4, QLF-001 Step 9 contract, candidate scanner evidence, `platform_core/policy/security_exceptions.py`, and historical `SEC-02`. Existing broad substring/wildcard matching is insufficient release waiver proof.

## Existing Files to Inspect

`platform_core/engine/release_qualification.py`, `platform_core/models/candidate_contract.py`, `platform_core/policy/security_exceptions.py`, `.nero-security-exceptions.yaml` (read only), and A4 governance.

## Files Allowed to Modify

`platform_core/policy/release_policy.py` and `tests/unit/test_release_policy.py` only, plus Antigravity-owned protocol replies.

## Files Prohibited from Modification

All other source/tests, exception YAML, catalog/manifests, audit ledger, application files, Docker/Jenkins/Terraform, Codex files and keys.

## Implementation Requirements

Provide typed release finding input (finding ID/fingerprint, scanner, severity, exact component and artifact digest, target path, fix state, observed time), waiver input (ID, exact finding ID/fingerprint, exact target/component/digest, named approver, justification, issued/expiry/revocation), and decision output compatible with QLF-001 Step 9. Every blocker must correlate to a scanner finding and exact release component; aggregate scanner counts alone cannot establish waiver coverage. Validate waiver active at evaluation time, not revoked, max 90-day TTL, correct severity/target/digest, exact finding correlation, and trusted approver policy. Reject wildcard or substring waiver scope for release blocking findings. Missing or contradictory scanner results and stale/unverified vulnerability DB fail closed. Allow only explicit approved waiver for HIGH/CRITICAL CVE; secrets and SAST blockers remain blocking unless a separately recorded policy decision expressly allows their type. Return per-finding disposition and policy version; never fabricate scanner evidence or mutate exception YAML.

## Security Requirements

Exact correlation defeats waiver reuse across CVE/component/digest. No silent acceptance on parser errors, absent findings inventory, revoked/expired waivers, or mismatched source commit. Do not log secret values.

## Test Requirements

Positive clean and exact-waiver cases; negative high/critical CVE, secret, SAST, wildcard, substring, wrong target/digest, expired, revoked, over-90-day, wrong approver, missing finding correlation and unverified DB cases. Test QLF-001 Step 9 interoperability. Run isolated and full regression.

## Acceptance Criteria

Only clean or exactly exempted eligible findings pass; all unexempted blockers fail; compatible Step 9 decision and tests pass.

## Infrastructure Restrictions

Read-only policy inputs; no live cloud/scanner/network mutation, audit append, commits or pushes.

## Expected Deliverables

Two allowed files, `ACK-TASK-A4-QLF-003.md`, and `RESULT-TASK-A4-QLF-003.md`.

## Completion Report Requirements

Decision contract, waiver matching rules, tests/counts, file inventory, preserved baselines, and limitations.

## Stop Conditions

Ask via protocol if QLF-001 Step 9 cannot consume the decision without prohibited edits. Publish result before QLF-004. Do not begin Phase 5.
