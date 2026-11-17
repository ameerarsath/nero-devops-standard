variable "aws_region" {
  description = "AWS region used by the SDK/provider while talking to Floci."
  type        = string
  default     = "us-east-1"
}

variable "floci_endpoint" {
  description = "Floci endpoint reachable from this Terraform process."
  type        = string
  default     = "http://localhost:4566"
}

variable "name_prefix" {
  description = "Short lowercase prefix used in resource names."
  type        = string
  default     = "sampleapp"

  validation {
    condition     = can(regex("^[a-z0-9-]{3,20}$", var.name_prefix))
    error_message = "name_prefix must be 3-20 characters and contain only lowercase letters, numbers, or hyphens."
  }
}

variable "environment" {
  description = "Environment label."
  type        = string
  default     = "local"

  validation {
    condition     = can(regex("^[a-z0-9-]{2,12}$", var.environment))
    error_message = "environment must be 2-12 lowercase letters, numbers, or hyphens."
  }
}

variable "tags" {
  description = "Additional tags applied to resources that support tags."
  type        = map(string)
  default     = {}
}
