terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile != "" ? var.aws_profile : null

  # Hard guardrail to avoid bootstrapping into wrong account
  allowed_account_ids = [var.target_aws_account_id]

  default_tags {
    tags = {
      Project     = "hotel-billing"
      Environment = var.environment
      Purpose     = "TerraformRemoteStateBootstrap"
      ManagedBy   = "Terraform"
    }
  }
}

locals {
  bucket_name = "${var.bucket_prefix}-${var.environment}-${var.target_aws_account_id}"
  table_name  = "${var.lock_table_prefix}-${var.environment}"
}

# 1. Dedicated S3 Bucket for Terraform Remote State
resource "aws_s3_bucket" "state" {
  bucket        = local.bucket_name
  force_destroy = false

  lifecycle {
    prevent_destroy = true
  }
}

# 2. Versioning enabled to safeguard against state corruption and enable state rollbacks
resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.state.id
  versioning_configuration {
    status = "Enabled"
  }
}

# 3. Server-side encryption enabled by default (AES256)
resource "aws_s3_bucket_server_side_encryption_configuration" "state" {
  bucket = aws_s3_bucket.state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# 4. Strict Public Access Block
resource "aws_s3_bucket_public_access_block" "state" {
  bucket                  = aws_s3_bucket.state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# 5. DynamoDB Lock Table for State Concurrency Control
resource "aws_dynamodb_table" "locks" {
  name         = local.table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  lifecycle {
    prevent_destroy = true
  }
}
