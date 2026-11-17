variable "bucket_name" {
  description = "Globally unique S3 bucket name when using real AWS."
  type        = string
}

variable "tags" {
  description = "Tags applied to the bucket."
  type        = map(string)
  default     = {}
}
