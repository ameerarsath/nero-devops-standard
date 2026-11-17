# Implementation Roadmap: Programme 2 (AI-Enhanced DevOps)
## Phases B0 through B6 Intelligence Evolution Plan

**Programme:** Nero Enterprise Universal DevOps Automation Platform  
**Strategy:** Deterministic Automation First, AI Intelligence Second  
**Scope:** Reusable AI Capabilities & Guardrails in `nero_devops_standard`  

---

## 1. Programme 2 Philosophy & Core Tenets

AI is an **additive intelligence layer**, not an authority. The deterministic platform core established in Programme 1 remains the authoritative system of record and execution gateway.

```
       +-------------------------------------------------------------+
       |               AI INTELLIGENCE LAYER                         |
       |  Copilot | Diagnostic Agent | Security & Risk Predictor     |
       +------------------------------+------------------------------+
                                      | Structured Proposals
                                      v
       +-------------------------------------------------------------+
       |               AI GUARDRAILS & EVALUATION                    |
       |  Schema Check | Policy Evaluation | Human Sign-off Gates   |
       +------------------------------+------------------------------+
                                      | Authorized Parameters
                                      v
+---------------------------------------------------------------------------+
|      DETERMINISTIC EXECUTION CORE (Programme 1 System of Record)          |
|  Jenkins Pipeline | Platform CLI | Terraform Engine | Audit Ledger        |
+---------------------------------------------------------------------------+
```

### Core Non-Negotiables:
1. **No Direct Execution**: AI agents cannot directly manipulate Docker daemon sockets, write directly to Terraform state files, or invoke AWS APIs unmediated.
2. **Explicit Tool Interfaces**: AI agents interact exclusively through typed, validated platform CLI commands and API endpoints.
3. **Fail Closed**: Any unparseable, ambiguous, or out-of-policy AI output results in immediate human escalation.
4. **Mandatory Human Approval**: Production changes and destructive operations require human authorization under all circumstances.

---

## 2. Autonomy Tiers (Levels 1 to 5)

| Autonomy Tier | Operational Name | Permitted Capabilities | Execution Boundary | Human Role |
|---|---|---|---|---|
| **Level 1** | Informational | Read pipeline logs, parse specifications, explain architecture and runbooks. | Read-Only | Consumer of information |
| **Level 2** | Advisory & Diagnostic | Correlate logs, diagnose build failures, propose test cases, calculate release risk scores. | Proposals Only (No mutations) | Reviewer of recommendations |
| **Level 3** | Prepared Action | Generate draft pull requests, stage configuration changes, prepare rollback requests. | Staged in staging branch / draft | Authorizer prior to execution |
| **Level 4** | Bounded Automation | Execute pre-approved deterministic recovery runbooks (container restart, cache clear) on non-prod environments. | Bounded by rate limits and whitelisted runbooks | Notified via alerts |
| **Level 5** | Production Adaptive | Execute authorized self-healing actions on production workloads within narrow policy bounds. | Restricted to reversible, non-destructive actions | Escalated on deviation; regular review |

---

## 3. Phase-by-Phase AI Evolution Plan

### Phase B0: AI Readiness and Data Foundation
- **Objectives**: Structure operational telemetry, logs, metrics, and documentation into machine-readable formats.
- **Key Deliverables**:
  - Structured JSON logs with unified correlation IDs (`trace_id`, `span_id`, `release_id`).
  - OpenAPI / JSON schema definitions for all Platform CLI tools.
  - Markdown-based runbook catalog formatted for retrieval-augmented generation (RAG).
- **Autonomy**: N/A (Data foundation).

### Phase B1: AI DevOps Copilot
- **Objectives**: Provide an interactive natural language assistant for developers and operators.
- **Capabilities**:
  - Explain pipeline execution failures and console errors in plain language.
  - Guide developers through authoring `app.spec.yaml`.
  - Answer questions regarding environment ports, active endpoints, and catalog authorizations.
- **Autonomy**: **Level 1 (Read-Only)**.

### Phase B2: AI Troubleshooting & Diagnostic Agent
- **Objectives**: Automate root-cause analysis for build and deployment failures.
- **Capabilities**:
  - Automatically analyze failed Jenkins builds.
  - Correlate container exit codes with application logs (e.g., missing `JWT_SECRET` placeholder, HikariCP timeout).
  - Pinpoint exact line of failure in source code or configuration.
  - Produce structured incident summaries and recommend verified remediation steps.
- **Autonomy**: **Level 2 (Diagnostic Proposals)**.

### Phase B3: AI Testing & Security Assistant
- **Objectives**: Enhance quality engineering and accelerate vulnerability triage.
- **Capabilities**:
  - Inspect Git diffs to generate missing unit and integration test cases.
  - Analyze Trivy container vulnerability reports to filter out false positives and prioritize reachable CVEs.
  - Propose dependency upgrades with lockfile diffs.
- **Autonomy**: **Level 2 (Advisory) / Level 3 (Draft PRs)**.

### Phase B4: AI Release & Deployment Intelligence
- **Objectives**: Predict deployment risk and optimize release rollout strategies.
- **Capabilities**:
  - Analyze commit velocity, test coverage changes, and infrastructure diffs.
  - Calculate release risk score (0 to 100).
  - Recommend rollout strategies (canary percentage, bake time).
  - Advise when an automated rollback is recommended based on anomaly detection in post-deploy metrics.
- **Autonomy**: **Level 2 (Risk Scoring & Recommendations)**.

### Phase B5: Bounded Autonomous Operations
- **Objectives**: Introduce self-healing capabilities for routine, well-understood operational incidents.
- **Capabilities**:
  - Automatically detect container crashes (OOMKilled, hung event loops) in develop and QA.
  - Trigger predefined, non-destructive recovery runbooks (restart container, release stale port).
  - Verify recovery using synthetic health probes.
  - Log complete diagnostic bundle and recovery action to the audit ledger.
- **Autonomy**: **Level 4 (Bounded Non-Production Automation)**.

### Phase B6: Adaptive DevOps Optimization
- **Objectives**: Continuously analyze operational efficiency, pipeline speed, and resource costs.
- **Capabilities**:
  - Identify redundant build steps and optimize Docker layer caching.
  - Rightsize container CPU and memory allocations based on actual utilization patterns.
  - Recommend non-production idle shutdown schedules to minimize cloud spend.
  - Propose continuous improvements to the platform standard.
- **Autonomy**: **Level 5 (Continuous Analysis with Human-Approved Policies)**.

---

## 4. Evaluation and Safety Metrics

Before advancing any AI agent to higher autonomy tiers, it must be evaluated against the following benchmarks:

1. **Diagnostic Precision**: Greater than 95% accuracy in root-cause identification across benchmark failure datasets.
2. **Zero Unauthorized Actions**: 0 tool calls executed outside authorized schema boundaries.
3. **Prompt Injection Resilience**: 100% rejection of adversarial prompt injection attempts embedded in application logs or commit messages.
4. **False Positive Rate**: Less than 2% false alarm rate on release risk predictions.
5. **Recovery Verification**: 100% of autonomous recovery actions followed by automated synthetic verification checks.
