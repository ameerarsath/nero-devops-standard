# ONBOARDING GUIDE: REUSING THE NERO DEVOPS STANDARD ON A NEW APPLICATION

This guide explains how to onboard ANY application onto the **Nero Enterprise DevOps Standard** in under 10 minutes.

---

## Step 1: Copy the DevOps Standard into your Application Repository

Copy the `nero_devops_standard` folder into your new repository root, or reference it as a submodule/shared module:

```bash
# In your target application repository root:
cp -r /path/to/nero_devops_standard/platform_core .
cp -r /path/to/nero_devops_standard/ci-cd .
cp -r /path/to/nero_devops_standard/platform_config.yaml .
```

---

## Step 2: Define your Application Specification (`app.spec.yaml`)

In your repository root (or under `applications/<your-app-id>/`), create `app.spec.yaml` using the template at `nero_devops_standard/templates/app.spec.template.yaml`:

```yaml
apiVersion: platform.enterprise.com/v1
kind: Application

metadata:
  name: "order-service"                  # Application ID
  version: "1.0.0"
  description: "Enterprise Order Processing Service"
  owner: "team-commerce@enterprise.com"

spec:
  components:
    - name: "api"
      type: "container-service"
      source:
        context: "."
        dockerfile: "Dockerfile"
      build:
        adapter: "dockerfile"
        target_stage: "runtime"
      runtime:
        name: "nodejs"
        version: "22"
        port: 8080
        cpu_units: 256
        memory_mb: 512
        health_check:
          path: "/health"
          interval_seconds: 15
          timeout_seconds: 5
          healthy_threshold: 2
      deployment:
        adapter: "ecs"
        desired_count: 1

  dependencies: []

  secrets:
    schema:
      - name: "database.password"
        description: "Postgres Password"
        required: true
```

Validate your specification:
```bash
python -m platform_core.engine.cli validate --spec app.spec.yaml
```

---

## Step 3: Register your Application in the Central Trust Catalog

Add your application entry to `platform_core/catalog/applications.yaml`:

```yaml
  - id: "order-service"
    display_name: "Enterprise Order Processing Service"
    trusted_repository: "https://github.com/my-org/order-service.git"
    spec_path: "app.spec.yaml"
    allowed_branches:
      - "main"
      - "release/*"
    allowed_environments:
      - "develop"
      - "qa"
      - "prod"
    allowed_platforms:
      - "floci-local"
      - "aws"
    allowed_topologies:
      - "multi_account"
      - "single_account"
    permitted_build_adapters:
      - "dockerfile"
    permitted_deployment_adapters:
      - "ecs"
    security_tier: "tier-2-standard"
```

Verify that catalog authorization passes:
```bash
python -m platform_core.engine.cli check-catalog \
    --app order-service \
    --env develop \
    --platform floci-local \
    --topology multi_account \
    --spec app.spec.yaml
```

---

## Step 4: Register or Update the Jenkins Universal Job

Run the automated registration script to register or update the universal pipeline in your Jenkins server:

```bash
python ci-cd/scripts/create_universal_job.py
```

This creates or updates the job `universal-application-pipeline` in Jenkins.

---

## Step 5: Execute your First Build & Deployment

You can now trigger the deployment pipeline either from the Jenkins Web UI or using the CLI runner:

### Option A: Via Jenkins Web UI
1. Open Jenkins at `http://localhost:8080`.
2. Select job **`universal-application-pipeline`**.
3. Click **Build with Parameters**:
   - `APPLICATION`: `order-service`
   - `ENVIRONMENT`: `develop`
   - `TARGET_PLATFORM`: `floci` (or `floci-local` / `aws`)
   - `ACCOUNT_TOPOLOGY`: `multi_account`
   - `ACTION`: `DEPLOY`
4. Click **Build**.

### Option B: Via Automation CLI
```bash
python ci-cd/scripts/trigger_and_follow_pipeline.py \
    --app order-service \
    --env develop \
    --platform floci \
    --topology multi_account \
    --action DEPLOY
```

---

## Step 6: Promoting to QA (Zero Rebuild)

To promote the exact release built in `develop` to `qa` without recompiling:

```bash
python -m platform_core.engine.cli build-release \
    --app order-service \
    --spec app.spec.yaml \
    --release-id <release-id-from-dev>
```

Deploy to QA:
```bash
python -m platform_core.engine.cli deploy-container \
    --app order-service \
    --env qa \
    --platform floci-local \
    --topology multi_account \
    --component api \
    --image api:<release-id-from-dev> \
    --host-port 8092
```

The platform verifies the container OCI SHA-256 digest against the original manifest, guaranteeing identical binary bits in QA.

---

## Step 7: Performing a Governed Rollback

If a defect is detected in QA or Production, roll back instantly to any earlier immutable release without rebuilding:

```bash
python -m platform_core.engine.cli rollback \
    --app order-service \
    --env qa \
    --release-id <previous-stable-release-id> \
    --operator sops-admin \
    --ticket CHG-20261107-001 \
    --reason "Reverting to stable release due to issue #1024"
```

Then redeploy the restored release:
```bash
python -m platform_core.engine.cli deploy-container \
    --app order-service \
    --env qa \
    --platform floci-local \
    --topology multi_account \
    --component api \
    --image api:<previous-stable-release-id> \
    --host-port 8092
```

---

## Congratulations!
Your application is now fully onboarded with:
- Immutable OCI releases with SHA-256 cryptographic provenance.
- Multi-environment promotion with zero recompilation.
- Standardized health verification and container lifecycles.
- Tamper-evident cryptographic audit logs for every operational action.
- ITIL-compliant emergency rollback capabilities.
