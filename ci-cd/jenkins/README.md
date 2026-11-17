# Universal Jenkins CI/CD Standard

Reusable Jenkins configuration, shared-library examples, and pipeline starters for Java/Spring Boot, Node.js/React, Python, and Terraform.

This package includes a **local learning lab** with Jenkins and Docker-in-Docker, and reuses the Floci container you already installed. The Compose lab is for a trusted developer workstation only. It is not a production Jenkins topology.

## Requirements

- Docker Desktop with Docker Compose v2
- 6 GB or more RAM available to Docker is recommended for the full lab
- A browser at `http://localhost:8080`

## Start the local lab (Windows PowerShell)

From this repository root:

```powershell
docker compose up --build -d
docker compose ps
docker compose logs -f jenkins
```

Get the initial Jenkins unlock password:

```powershell
docker compose exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

Open http://localhost:8080, unlock Jenkins, create your administrator, and install the suggested plugins. The image also pre-installs the plugin set in `jenkins/plugins.txt`; restart Jenkins if the setup wizard asks you to. Plugin versions are not locked in this learning starter; pin and test them before a production rollout.

The Jenkins container reaches your already-running Floci instance through Docker Desktop at `http://host.docker.internal:4566`; Windows tools use `http://localhost:4566`. Keep your existing Floci container running. This Compose file intentionally does not create a second Floci container or claim port `4566`.

Stop the lab:

```powershell
docker compose down
```

Remove Jenkins and Docker-in-Docker volumes (DESTRUCTIVE to Jenkins jobs, configuration, and Docker build cache):

```powershell
docker compose down -v
```

## What is included

```text
jenkins/
  Dockerfile                 Local learning controller image
  plugins.txt                Jenkins plugins installed by the image
  casc/jenkins.yaml          Jenkins Configuration as Code baseline
pipelines/
  java/Jenkinsfile           Maven/Java pipeline starter
  nodejs/Jenkinsfile         Node.js/React pipeline starter
  python/Jenkinsfile         Python pipeline starter
  terraform/Jenkinsfile     Terraform fmt/validate/plan against Floci
shared-library/
  vars/standardDockerBuild.groovy
  vars/standardTerraformChecks.groovy
  README.md                  Register and use the library
examples/
  Dockerfile                 Minimal example application image
compose.yaml                 Jenkins + Docker-in-Docker local lab (reuses existing Floci)
```

## Connect a pipeline to a repository

Create a Pipeline or Multibranch Pipeline job, connect your Git repository, and choose the matching `Jenkinsfile` path. For Multibranch Pipeline, keep branch names consistent with your team's policy (for example `feature/*`, `develop`, and `main`). Add webhook integration separately in your Git provider and configure the corresponding Jenkins credentials.

Pipeline files assume the repository contains the expected project files:

- Java: Maven `pom.xml`, test suite, and optional Dockerfile.
- Node: `package.json`, lockfile, npm scripts (`test`, optional `lint`, and `build`), and optional Dockerfile.
- Python: `requirements.txt`, `pytest` test suite, and optional Dockerfile.
- Terraform: Terraform root under `infra/environments/local` and Floci reachable at `http://host.docker.internal:4566` from the Jenkins container.

The local learning image includes Maven, Node.js/npm, Python, Terraform, and Docker CLI, so the sample language pipelines can run on the built-in node. These examples build/test and optionally push images; they do not perform a production application deployment or Terraform apply. Add deployment steps for your chosen target (for example ECS, EC2, EKS, or Elastic Beanstalk) and gate production changes separately. This is only for a single-user lab. For production, change `agent any` to dedicated agent labels and set controller executors to `0`. If your repository layout differs, update `TF_ROOT` and `TF_DIR` in the Terraform Jenkinsfile.

## Jenkins credentials convention

Create credentials in **Manage Jenkins → Credentials**. Example IDs:

- `container-registry`: Username with password for your approved container registry.
- `aws-deploy-role`: Prefer workload identity / OIDC or an agent role; do not store long-lived AWS keys if role-based federation is available.
- `git-readonly`: Only when private SCM checkout requires it.

Never commit credentials, tokens, kubeconfigs, private keys, or `.env` files.

## Shared library

See `shared-library/README.md`. Register the repository under **Manage Jenkins → System → Global Pipeline Libraries** using the name `company-ci`, then call it with `@Library('company-ci') _` in a Jenkinsfile.

## Production architecture guidance

Do not run production builds on the Jenkins controller. Set controller executors to `0` and use isolated, ephemeral agents with labels such as `linux-java-docker`, `linux-node-docker`, `linux-python-docker`, and `linux-terraform`. Put agents on separate machines or isolated containers; grant Docker daemon access only to trusted workloads. Prefer rootless BuildKit/Buildah or a managed build service where feasible instead of exposing a privileged Docker daemon.

For production:

- Use a supported, patched Jenkins LTS image pinned to a version or digest.
- Back up `$JENKINS_HOME` and test restore procedures.
- Restrict controller and agent network access.
- Use matrix-based authorization / SSO, MFA at the identity provider, CSRF protection, and least privilege.
- Store secrets in a proper secrets manager and use short-lived AWS credentials (OIDC / IAM roles).
- Require approval and reviewed Terraform plans before production apply.
- Add artifact retention, audit logging, dependency scanning, container scanning, and SBOM generation according to your policy.
- Keep the Docker-in-Docker service in this local lab only; it is privileged and grants powerful host-adjacent capabilities.

## References

- Jenkins Pipeline: https://www.jenkins.io/doc/book/pipeline/
- Jenkins Docker Pipeline: https://www.jenkins.io/doc/book/pipeline/docker/
- Jenkins Configuration as Code: https://www.jenkins.io/projects/jcasc/
- Jenkins Shared Libraries: https://www.jenkins.io/doc/book/pipeline/shared-libraries/
- Floci: https://github.com/floci-io/floci
