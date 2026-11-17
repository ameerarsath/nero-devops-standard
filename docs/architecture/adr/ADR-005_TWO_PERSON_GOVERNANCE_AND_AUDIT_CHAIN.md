# Architecture Decision Record: ADR-005
## Title: Two-Person Production Governance & Cryptographic Audit Hash Chaining

**Status:** Accepted  
**Date:** 2026-11-08  
**Context:**  
Enterprise production environments require strict access control, separation of duties, and non-repudiation. Single-approver or informal Slack approvals fail compliance standards (SOC 2, ISO 27001). Furthermore, flat audit logs can be retroactively altered or deleted.

**Decision:**  
1. **Two-Person Production Governance**:
   - Production deployments strictly require two independent approvals:
     - **Gate 1 (QA Technical Sign-off)**: Verified by QA/Automation Lead (`qa.lead`), certifying test completion.
     - **Gate 2 (Operations/SRE Release Approval)**: Verified by SRE Lead (`sre.lead`), validating maintenance window and ITIL Change Ticket ID (`CHG-*`).
   - Separation of duties is enforced: `qa_approver != ops_approver`. If the same user attempts both approvals, the pipeline halts with `[GOVERNANCE_VIOLATION]`.
2. **Cryptographic Audit Ledger**:
   - Every operational event (Build, Plan, Apply, Deploy, Verify, Rollback, Governance Approval) is recorded in `audit_log.jsonl`.
   - Each entry includes a canonical JSON serialization, a timestamp, and a SHA-256 hash computed over the payload and the preceding entry's hash (`previous_hash`).
   - The platform provides a verification tool (`verify_audit_ledger`) that validates the entire chain from genesis to head.

**Consequences:**  
- Positive: Guaranteed compliance with enterprise separation-of-duties mandates.
- Positive: Tamper-evident ledger that detects any retroactive tampering or deletion of deployment history.
