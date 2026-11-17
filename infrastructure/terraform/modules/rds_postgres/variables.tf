variable "db_identifier" {
  description = "Identifier for the RDS instance."
  type        = string
}

variable "engine_version" {
  description = "PostgreSQL engine version."
  type        = string
  default     = "15.7"
}

variable "instance_class" {
  description = "Instance class for RDS."
  type        = string
  default     = "db.t3.micro"
}

variable "allocated_storage" {
  description = "Allocated storage in gigabytes."
  type        = number
  default     = 20
}

variable "db_name" {
  description = "Default database name."
  type        = string
  default     = "hotel_billing"
}

variable "username" {
  description = "Master username for database."
  type        = string
  default     = "postgres"
}

variable "password" {
  description = "Master password for database."
  type        = string
  default     = "postgres"
  sensitive   = true
}

variable "tags" {
  description = "Tags to apply to the RDS instance."
  type        = map(string)
  default     = {}
}

variable "publicly_accessible" {
  description = "Whether the database is publicly accessible."
  type        = bool
  default     = true
}

variable "skip_final_snapshot" {
  description = "Whether to skip final snapshot before deleting the database."
  type        = bool
  default     = true
}

variable "db_subnet_group_name" {
  description = "Name of DB subnet group for private VPC placement (null for default/mock)."
  type        = string
  default     = null
}

variable "vpc_security_group_ids" {
  description = "List of VPC security group IDs to associate with RDS (null for default)."
  type        = list(string)
  default     = null
}

variable "deletion_protection" {
  description = "If true, the database can't be deleted without modifying this setting (Production safeguard)."
  type        = bool
  default     = false
}

variable "multi_az" {
  description = "Specifies if the RDS instance is Multi-AZ (Production high availability)."
  type        = bool
  default     = false
}

variable "backup_retention_period" {
  description = "The days to retain backups for. Must be 1 or greater for PITR."
  type        = number
  default     = null
}

variable "backup_window" {
  description = "The daily time range (in UTC) during which automated backups are created."
  type        = string
  default     = null
}

variable "maintenance_window" {
  description = "The window to perform maintenance in (UTC)."
  type        = string
  default     = null
}
