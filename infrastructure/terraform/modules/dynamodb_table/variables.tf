variable "table_name" {
  description = "DynamoDB table name."
  type        = string
}

variable "hash_key" {
  description = "String partition key attribute name."
  type        = string
  default     = "id"
}

variable "tags" {
  description = "Tags applied to the table."
  type        = map(string)
  default     = {}
}
