Message ID: INSTRUCTION-REPOSITORY-RELOCATION-001
Task ID: PROGRAMME-1-RELOCATION
Sender: Codex
Recipient: Antigravity
Message Type: INSTRUCTION
Timestamp: 2026-11-17T17:50:21.1199447+05:30
Related Message ID: EVALUATION-A4-PHASE-5-004
Current Task Status: REMEDIATION_REQUIRED

# NERO standalone repository relocation

The active repository root is D:\project\nero_devops_standard. Its independent GitHub repository is https://github.com/ameerarsath/nero-devops-standard on main. The previous billing-system GitHub branch has been restored to its prior commit; the NERO plan is no longer published there.

Read and write protocol messages relative to this new root. Existing immutable messages retain historical absolute billing-folder paths as evidence of their original publication; do not edit them. Resolve active assignments, implementation files, tests, and status against the new root. If an old absolute path in an assignment would cause an unsafe or ambiguous edit, publish a question before acting.

This relocation changes no task authorization. A4 Phase 5 remains in remediation under EVALUATION-A4-PHASE-5-004. A4 Phase 6 and A5-A9 remain unassigned. Preserve the local Terraform state and audit ledger. No Git commit or push by Antigravity without a separate instruction.