variable "aws_region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "ap-south-1"
}

variable "name_prefix" {
  description = "Short lowercase prefix used in resource names."
  type        = string
  default     = "sample-node"

  validation {
    condition     = can(regex("^[a-z0-9-]{3,20}$", var.name_prefix))
    error_message = "name_prefix must be 3-20 characters and contain only lowercase letters, numbers, or hyphens."
  }
}

variable "environment" {
  description = "Environment label."
  type        = string
  default     = "canary"

  validation {
    condition     = can(regex("^[a-z0-9-]{2,12}$", var.environment))
    error_message = "environment must be 2-12 lowercase letters, numbers, or hyphens."
  }
}

variable "tags" {
  description = "Additional AWS resource tags."
  type        = map(string)
  default     = {}
}

variable "aws_account_id" {
  description = "Target AWS Account ID enforced via allowed_account_ids."
  type        = string
  default     = ""
}

variable "role_arn" {
  description = "IAM Role ARN to assume via STS AssumeRole for cross-account deployments."
  type        = string
  default     = ""
}

variable "container_image" {
  description = "Full container image URI with tag or digest (e.g., from ECR)."
  type        = string
  default     = ""
}

variable "container_port" {
  description = "Port the container listens on."
  type        = number
  default     = 8080
}

variable "vpc_cidr" {
  description = "CIDR block for sandbox VPC."
  type        = string
  default     = "10.100.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones for multi-AZ ALB deployment."
  type        = list(string)
  default     = ["ap-south-1a", "ap-south-1b"]
}

variable "allowed_ingress_cidrs" {
  description = "Allowed CIDR blocks for ALB HTTP ingress."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
