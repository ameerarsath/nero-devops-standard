variable "name_prefix" {
  description = "Resource prefix."
  type        = string
  default     = "billing"
}

variable "environment" {
  description = "Environment identifier."
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where the ALB and Target Group reside."
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnet IDs where the ALB is placed."
  type        = list(string)
}

variable "security_group_ids" {
  description = "Security group IDs associated with the ALB."
  type        = list(string)
}

variable "backend_port" {
  description = "Port on which backend tasks listen."
  type        = number
  default     = 8082
}

variable "health_check_path" {
  description = "Path for ALB health checks."
  type        = string
  default     = "/"
}

variable "tags" {
  description = "Resource tags."
  type        = map(string)
  default     = {}
}
