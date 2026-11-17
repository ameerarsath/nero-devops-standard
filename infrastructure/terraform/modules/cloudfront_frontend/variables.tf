variable "bucket_name" {
  description = "Name of the private S3 bucket hosting frontend static assets."
  type        = string
}

variable "name_prefix" {
  description = "Prefix for CloudFront distribution and OAC resources."
  type        = string
  default     = "billing"
}

variable "environment" {
  description = "Target environment name (e.g. prod, qa, develop)."
  type        = string
  default     = "prod"
}

variable "tags" {
  description = "Resource tags."
  type        = map(string)
  default     = {}
}
