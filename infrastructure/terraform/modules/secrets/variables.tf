variable "name_prefix" {
  description = "Prefix for the secret name."
  type        = string
  default     = "billing"
}

variable "environment" {
  description = "Environment name (develop, qa, prod)."
  type        = string
}

variable "secret_name" {
  description = "Explicit name for the secret. Defaults to billing-{env}/app-secrets if empty."
  type        = string
  default     = ""
}

variable "aws_account_id" {
  description = "Dedicated AWS account ID associated with this environment."
  type        = string
  default     = ""
}

variable "db_username" {
  description = "Database master username."
  type        = string
  default     = "postgres"
}

variable "db_password" {
  description = "Database master password."
  type        = string
  sensitive   = true
}

variable "db_name" {
  description = "Database name."
  type        = string
}

variable "db_endpoint" {
  description = "Database endpoint."
  type        = string
  default     = "postgres:5432"
}

variable "jwt_secret" {
  description = "HMAC SHA-256 secret for signing JWTs."
  type        = string
  sensitive   = true
  default     = ""
}

variable "jwt_expiration" {
  description = "JWT expiration time in milliseconds."
  type        = string
  default     = "86400000"
}

variable "frontend_url" {
  description = "URL for the React frontend."
  type        = string
  default     = ""
}

variable "backend_url" {
  description = "URL for the Spring Boot backend."
  type        = string
  default     = ""
}

variable "invoice_base_url" {
  description = "Base URL for invoice verification."
  type        = string
  default     = ""
}

variable "tags" {
  description = "Resource tags."
  type        = map(string)
  default     = {}
}
