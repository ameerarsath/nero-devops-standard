variable "target_aws_account_id" {
  description = "Target 12-digit AWS Account ID for bootstrap verification."
  type        = string

  validation {
    condition     = can(regex("^[0-9]{12}$", var.target_aws_account_id))
    error_message = "target_aws_account_id must be exactly 12 numeric digits."
  }
}

variable "aws_region" {
  description = "AWS region where state storage and lock table will reside."
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "Named AWS CLI profile to use for bootstrap authentication."
  type        = string
  default     = ""
}

variable "environment" {
  description = "Environment identifier (develop, qa, or prod)."
  type        = string

  validation {
    condition     = contains(["develop", "qa", "prod"], var.environment)
    error_message = "environment must be one of: develop, qa, prod."
  }
}

variable "bucket_prefix" {
  description = "Prefix for the remote state bucket name."
  type        = string
  default     = "billing-terraform-state"
}

variable "lock_table_prefix" {
  description = "Prefix for the DynamoDB lock table name."
  type        = string
  default     = "billing-terraform-locks"
}
