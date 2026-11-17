variable "cluster_name" {
  description = "Name of the ECS cluster."
  type        = string
}

variable "task_family" {
  description = "Task definition family name."
  type        = string
}

variable "service_name" {
  description = "Name of the ECS service."
  type        = string
}

variable "container_name" {
  description = "Name of the backend container."
  type        = string
  default     = "billing-backend"
}

variable "image" {
  description = "Docker image for the backend container."
  type        = string
  default     = "billing-backend:local"
}

variable "container_port" {
  description = "Port exposed by the backend container."
  type        = number
  default     = 8082
}

variable "host_port" {
  description = "Host port mapped to the backend container."
  type        = number
  default     = 8082
}

variable "desired_count" {
  description = "Desired number of running tasks."
  type        = number
  default     = 1
}

variable "environment_variables" {
  description = "Environment variables passed to the container."
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}

variable "tags" {
  description = "Tags applied to ECS resources."
  type        = map(string)
  default     = {}
}
