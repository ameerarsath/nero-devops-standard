# NERO Markdown communication protocol

## Ownership

Codex alone writes `01_codex_to_antigravity/`, `04_status/`, top-level protocol documents, and archives. Antigravity alone writes `02_antigravity_to_codex/`. Shared files are read by both; the designated author of each shared file alone publishes it. Neither agent edits another agent's message.

## Message contract

Each message has `Message ID`, `Task ID`, `Sender`, `Recipient`, `Message Type`, `Timestamp` (ISO 8601 with offset), `Related Message ID` (or `None`), and `Current Task Status`. Message IDs and final filenames are unique. Examples: `TASK-A4-MAN-001.md`, `ACK-TASK-A4-MAN-001.md`, `QUESTION-TASK-A4-MAN-001-001.md`, `ANSWER-TASK-A4-MAN-001-001.md`, `RESULT-TASK-A4-MAN-001.md`, `EVALUATION-TASK-A4-MAN-001.md`. For further messages of a type, append a sequence or timestamp before `.md`; never replace an earlier file. Evaluation messages belong in `01_codex_to_antigravity/instructions/`.

Publish by writing a temporary file in the destination directory, flushing and closing it, then atomically renaming it to an unused final filename. If that name exists, choose another unique name. Never edit or overwrite a published message. Archive only after the task closes.

## Lifecycle

Allowed statuses: `DRAFT`, `READY`, `ASSIGNED`, `ACKNOWLEDGED`, `IN_PROGRESS`, `BLOCKED`, `QUESTION_PENDING`, `IMPLEMENTATION_COMPLETED`, `UNDER_EVALUATION`, `REMEDIATION_REQUIRED`, `ACCEPTED`, `REJECTED`, `CANCELLED`.

Codex owns the authoritative status in `04_status/TASK_REGISTER.md`; Antigravity reports transitions through new messages. Implementation completion starts independent evaluation and never implies acceptance. Codex checks the Git diff, source, tests, security and compatibility invariants, infrastructure and audit baselines, and assignment criteria. Evaluation verdicts are `ACCEPTED`, `ACCEPTED_WITH_REMEDIATIONS`, `REMEDIATION_REQUIRED`, or `REJECTED`. Stop reviewing once objective criteria are met.

## Questions and blockers

Antigravity stops the affected work and publishes a question in `02_antigravity_to_codex/questions/` with exact ambiguity, paths, options, and impact. Codex replies in `01_codex_to_antigravity/clarifications/` with a related message ID. Security, architecture, scope, and authorization decisions cannot be guessed. Minor specified implementation details use engineering judgement. Blockers go in `02_antigravity_to_codex/blockers/`.

## Session rhythm and governance

No filesystem polling loops. Inspect incoming messages on session start, user status request, or explicit communication event. Before assignment, verify the applicable owner authorization. The original owner record left Gate 3 pending; `01_codex_to_antigravity/instructions/DECISION-A4-GATE3-001.md` records the later limited A4 Gate 3 approval. Each implementation task still requires a specific published assignment. Preserve local-only Floci/Docker architecture and the authoritative audit ledger, subject only to separately scoped append-only release audit work. Do not commit, push, provision real AWS resources, run destructive Terraform or Docker operations, or erase existing work without explicit authorization.
