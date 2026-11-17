variable "queue_name" {
  description = "Queue name."
  type        = string
}

variable "message_retention_seconds" {
  description = "How long messages remain in the queue."
  type        = number
  default     = 345600
}

variable "tags" {
  description = "Tags applied to the queue."
  type        = map(string)
  default     = {}
}
