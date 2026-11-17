variable "aws_region" {
  description = "AWS region used for Floci SDK compatibility."
  type        = string
  default     = "us-east-1"
}

variable "aws_account_id" {
  description = "Dedicated AWS Account ID for Production."
  type        = string
  default     = "777788889999"
}

variable "floci_endpoint" {
  description = "Floci endpoint reachable from this Terraform process."
  type        = string
  default     = "http://localhost:4566"
}

variable "name_prefix" {
  description = "Short prefix used in naming environment resources."
  type        = string
  default     = "billing-prod"

  validation {
    condition     = can(regex("^[a-z0-9-]{3,20}$", var.name_prefix))
    error_message = "name_prefix must be 3-20 characters and contain only lowercase letters, numbers, or hyphens."
  }
}

variable "environment" {
  description = "Environment identifier."
  type        = string
  default     = "prod"
}

variable "db_instance_class" {
  description = "RDS instance class."
  type        = string
  default     = "db.t3.medium"
}

variable "db_allocated_storage" {
  description = "Allocated storage in GB."
  type        = number
  default     = 50
}

variable "db_name" {
  description = "Default database name."
  type        = string
  default     = "hotel_billing_prod"
}

variable "db_username" {
  description = "Master username for database."
  type        = string
  default     = "postgres"
}

variable "db_password" {
  description = "Master password for database."
  type        = string
  default     = "postgres_prod"
  sensitive   = true
}

variable "jwt_secret" {
  description = "HMAC SHA-256 secret for signing JWTs in Production."
  type        = string
  default     = "7589788D7B925595589851914164516740604D6F8473877680798F7C93569659"
  sensitive   = true
}

variable "jwt_expiration" {
  description = "JWT expiration time in milliseconds."
  type        = string
  default     = "28800000"
}

variable "frontend_url" {
  description = "Production frontend application URL."
  type        = string
  default     = "http://localhost:3003"
}

variable "backend_url" {
  description = "Production backend application URL."
  type        = string
  default     = "http://localhost:8088"
}

variable "backend_image" {
  description = "Docker image repository and tag for backend container."
  type        = string
  default     = "billing-backend:prod"
}

variable "ecs_host_port" {
  description = "Host port mapped to backend ECS container."
  type        = number
  default     = 8089
}

variable "tags" {
  description = "Resource tags."
  type        = map(string)
  default     = {}
}
