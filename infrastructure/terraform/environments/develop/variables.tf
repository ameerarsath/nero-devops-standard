variable "aws_region" {
  description = "AWS region used for Floci SDK compatibility."
  type        = string
  default     = "us-east-1"
}

variable "aws_account_id" {
  description = "Dedicated AWS Account ID for Development."
  type        = string
  default     = "111122223333"
}

variable "floci_endpoint" {
  description = "Floci endpoint reachable from this Terraform process."
  type        = string
  default     = "http://localhost:4566"
}

variable "name_prefix" {
  description = "Short prefix used in naming environment resources."
  type        = string
  default     = "billing-dev"

  validation {
    condition     = can(regex("^[a-z0-9-]{3,20}$", var.name_prefix))
    error_message = "name_prefix must be 3-20 characters and contain only lowercase letters, numbers, or hyphens."
  }
}

variable "environment" {
  description = "Environment identifier."
  type        = string
  default     = "develop"
}

variable "db_instance_class" {
  description = "RDS instance class."
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Allocated storage in GB."
  type        = number
  default     = 20
}

variable "db_name" {
  description = "Default database name."
  type        = string
  default     = "hotel_billing_dev"
}

variable "db_username" {
  description = "Master username for database."
  type        = string
  default     = "postgres"
}

variable "db_password" {
  description = "Master password for database."
  type        = string
  default     = "postgres_dev"
  sensitive   = true
}

variable "jwt_secret" {
  description = "HMAC SHA-256 secret for signing JWTs in Development."
  type        = string
  default     = "5367566B59703373367639792F423F4528482B4D6251655468576D5A71347437"
  sensitive   = true
}

variable "jwt_expiration" {
  description = "JWT expiration time in milliseconds."
  type        = string
  default     = "86400000"
}

variable "frontend_url" {
  description = "Development frontend application URL."
  type        = string
  default     = "http://localhost:3001"
}

variable "backend_url" {
  description = "Development backend application URL."
  type        = string
  default     = "http://localhost:8084"
}

variable "backend_image" {
  description = "Docker image repository and tag for backend container."
  type        = string
  default     = "billing-backend:develop"
}

variable "ecs_host_port" {
  description = "Host port mapped to backend ECS container."
  type        = number
  default     = 8085
}

variable "tags" {
  description = "Resource tags."
  type        = map(string)
  default     = {}
}
