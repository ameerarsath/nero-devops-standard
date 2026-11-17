# Universal Terraform AWS Starter

A reusable Terraform starter for AWS-shaped infrastructure, with two execution targets:

- `environments/local`: Floci local AWS emulator (`http://localhost:4566`).
- `environments/aws`: real AWS using the standard AWS credential chain.

The starter intentionally includes a small, understandable baseline: S3, SQS, and DynamoDB. The S3 module enables bucket versioning, default SSE-S3 encryption, and all four public-access blocks. Extend it by adding modules for the services your application actually needs. If you already have Floci running on port `4566`, do not start another Floci container; skip the Compose start command and use the existing instance.

## Requirements

- Terraform CLI >= 1.10 and < 2.0
- Docker Desktop with Docker Compose v2 (for local Floci use)
- AWS CLI v2 (optional, useful for verifying local resources)
- For real AWS: an AWS account and a least-privilege IAM identity/profile

## Quick start on Windows PowerShell (Floci)

From the repository root. Since you already have Floci running, keep it running and skip starting another emulator. (For a fresh machine only, start Floci with `docker compose up -d`.)

```powershell
terraform fmt -recursive
Set-Location environments/local
terraform init
terraform validate
terraform plan
terraform apply
```

Confirm the resources in Floci (AWS CLI required):

```powershell
aws --endpoint-url http://localhost:4566 s3 ls
aws --endpoint-url http://localhost:4566 sqs list-queues
aws --endpoint-url http://localhost:4566 dynamodb list-tables
```

Destroy the test resources and stop Floci:

```powershell
terraform destroy
Set-Location ../..
# Run this only if you started Floci with this repository's Compose file.
docker compose down
```

When you start Floci with this repository's Compose file, its data is persisted under `./floci-data`. To remove that emulator data, stop that Compose stack first and delete the folder deliberately.

## Real AWS

Use a dedicated AWS profile or an IAM role. Do not put access keys in `.tf` files or commit credentials.

```powershell
aws configure --profile dev
$env:AWS_PROFILE = "dev"
$env:AWS_REGION = "ap-south-1"
terraform fmt -recursive
Set-Location environments/aws
terraform init
terraform validate
terraform plan
```

Review the plan carefully before `terraform apply`. This starter creates billable cloud resources when used against real AWS. Run `terraform destroy` when the test environment is no longer required.

## Structure

```text
modules/                    Reusable resource modules
  s3_bucket/
  sqs_queue/
  dynamodb_table/
environments/
  local/                    Floci provider endpoints; local state
  aws/                      Real AWS provider; local state until remote backend configured
compose.yaml                Floci emulator for local practice
scripts/                    PowerShell helper commands
```

## Reuse in another application

1. Copy this repository or reference the module directories from your infrastructure repository.
2. Create a new environment root (or a new application root) that calls the modules.
3. Set `name_prefix`, `environment`, `aws_region`, and `tags` through variables / `.tfvars`.
4. Keep Terraform state separate for each application and environment.
5. Add only the modules and AWS endpoints required by that application.

## State management and production notes

- Both example roots use Terraform's local state by default to keep the lab simple. Run `terraform init`, review the generated `.terraform.lock.hcl`, and commit that lock file to pin provider selections.
- Never commit `terraform.tfstate`, `terraform.tfstate.backup`, `.terraform/`, or secret `.tfvars` files.
- Before team or production use, configure a dedicated remote backend (for example, an encrypted S3 bucket with versioning and Terraform S3 lockfile support), with a separate state key for each app/environment. Bootstrap the backend separately before migrating state.
- Do not use Floci as production infrastructure or production Terraform state storage.
- Use separate AWS accounts or strong account/environment boundaries for dev, staging, and production.
- Use least-privilege IAM, encryption, logging, budget alerts, and reviewed plans.
- Floci is an emulator, not a guarantee of full AWS behavioural parity. Validate important integrations in a controlled AWS account before production.

## Adding an AWS service

For a service used in `environments/local`, add its endpoint to the `endpoints` block in `environments/local/providers.tf`. Floci documents that each Terraform-managed AWS service must have its own endpoint configured. Check the Floci service support matrix before adding a resource.

## References

- Floci Terraform guide: https://floci.io/floci/getting-started/terraform/
- Floci S3 support matrix: https://floci.io/floci/services/s3/
- Floci repository: https://github.com/floci-io/floci
- Terraform AWS provider: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
- Terraform language: https://developer.hashicorp.com/terraform/language
