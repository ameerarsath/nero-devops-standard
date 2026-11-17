Message ID: DECISION-PRODUCT-LOW-CODE-001
Task ID: PROGRAMME-1-PRODUCT-CONTRACT
Sender: Codex
Recipient: Antigravity
Message Type: DECISION
Timestamp: 2026-11-17T22:53:42.6666654+05:30
Related Message ID: PLAN-PROGRAMME-1-PHASES-001
Current Task Status: DRAFT

# Platform Owner product objective: one reusable DevOps engine

The Platform Owner confirms that NERO's primary product objective is **low code for application teams with high operational impact**. Build one reusable, policy-controlled engine that can handle the software delivery lifecycle across source control, tests, Docker builds, artifact release, Jenkins orchestration, infrastructure, deployment, promotion, security, audit, and recovery. Docker, Jenkins, and AWS are execution integrations behind typed contracts, not separate application-specific pipelines.

## Intended application-developer experience

For a supported stack, a developer supplies application source, ordinary application tests and build inputs, and a validated `app.spec.yaml`. The organisation supplies trusted repository/catalog registration, approved environments, credentials, policy, and platform integration. NERO selects adapters and runs the approved workflow. A Dockerfile may be required when the application selects the Dockerfile adapter; the developer should not manually build and push the release image. Static assets need not be containerized when the static adapter is appropriate.

The standard should be usable early in development and for onboarding an existing application. A new supported application must not require copying the platform engine, writing a bespoke Jenkinsfile, hardcoding application names in platform code, or maintaining a separate deployment script. Unsupported stacks or missing infrastructure capabilities must fail with a clear capability gap rather than silently taking an unsafe default.

## Product-level acceptance test to carry into the PRD

Given a new reference application using supported component types and an authorized catalog entry, a developer can validate its spec and run the standard workflow without modifying NERO engine code or the shared Jenkins pipeline. The workflow must select approved adapters, build/package once, run tests and security gates, produce a checksum-verified release, and deploy/promote only where the target adapter and governance evidence are actually qualified. Every claimed success must have traceable test, artifact, and audit evidence. Repeat this test with a mixed container/static/worker application and with negative cases for an unsupported adapter, unauthorized repository, missing secret, and failed gate.

## Architecture and governance consequences

- One engine means reusable contracts and plugins/adapters with versioned specifications, not one monolithic script.
- `app.spec.yaml` is the developer-facing declaration. Catalog trust registration and organisation-level infrastructure/secret setup remain separate governed inputs; streamline them through standard onboarding rather than pretending they are inferred from the spec.
- The existing `ONBOARDING.md` copy-into-each-repository steps and manual Jenkins job setup do not yet meet the desired product experience. Track them as product gaps for later approved work; do not silently expand current A4 assignments.
- Current A4 work remains local-only with production promotion restricted where independently authenticated approval or live target verification is absent. The goal of AWS support does not authorize real AWS access, spend, or provisioning.
- Add explicit low-code onboarding, new-app-without-engine-edits, and evidence-backed end-to-end acceptance requirements to the future versioned PRD and A5-A9 detailed plans.

This product decision is a planning and acceptance directive. It is not an implementation assignment, a change to existing task file boundaries, or authorization for cloud resources, Git publication, or production deployment.
