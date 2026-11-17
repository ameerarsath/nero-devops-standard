variable "name_prefix" {
  description = "Resource prefix for naming."
  type        = string
  default     = "billing"
}

variable "environment" {
  description = "Environment identifier (develop, qa, prod)."
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the dedicated VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of at least two Availability Zones."
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "tags" {
  description = "Resource tags."
  type        = map(string)
  default     = {}
}
