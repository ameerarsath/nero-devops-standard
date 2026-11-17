# Remote Terraform State Bootstrap & Locking Architecture

This module provisions foundational infrastructure for remote Terraform state management across independent AWS accounts (`develop`, `qa`, `prod`).

---

## 1. State Locking Strategy: S3 Native vs DynamoDB

Terraform v1.10+ introduced **S3 Native State Locking** using S3 conditional write semantics (`If-None-Match: *`).

### Preferred Strategy: Native S3 Locking (`use_lockfile = true`)
- **How it works**: Terraform creates a temporary `.terraform.tfstate.lock.info` lockfile directly inside the S3 bucket alongside the state file using atomic conditional writes.
- **Benefits**:
  - Eliminates external DynamoDB dependency and billing.
  - Keeps state and locking within the same security boundary.
  - Native atomic consistency guarantees.
- **Backend Configuration**:
  ```hcl
  bucket       = "billing-terraform-state-<env>-<account_id>"
  key          = "environments/<env>/terraform.tfstate"
  region       = "us-east-1"
  encrypt      = true
  use_lockfile = true
  ```

### Optional / Legacy Strategy: DynamoDB Locking Table
- Retained in this module for backward compatibility or organizations requiring central DynamoDB state locks.
- Uses `billing-terraform-locks-<env>` table with `LockID` (String) partition key.

---

## 2. Required IAM Permissions

### IAM Policy for S3 Native State Locking (Preferred)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "TerraformStateBucketAccess",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation",
        "s3:GetBucketVersioning"
      ],
      "Resource": "arn:aws:s3:::billing-terraform-state-*"
    },
    {
      "Sid": "TerraformStateFileAndLockAccess",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::billing-terraform-state-*/*"
    }
  ]
}
```

### Additional IAM Policy if DynamoDB Locking is Used
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "TerraformDynamoDBLocking",
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:DeleteItem"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/billing-terraform-locks-*"
    }
  ]
}
```

---

## 3. Bootstrap Procedure

Run this module once for each dedicated AWS account:

```bash
cd infrastructure/terraform/bootstrap
terraform init
terraform apply \
  -var="environment=develop" \
  -var="target_aws_account_id=<DEVELOPMENT_ACCOUNT_ID>" \
  -var="aws_profile=billing-develop"
```

Repeat with `environment=qa` and `environment=prod` in their respective AWS accounts.
Copy the generated `backend_hcl_snippet_s3_native` into `backend.hcl` in that environment's directory.
