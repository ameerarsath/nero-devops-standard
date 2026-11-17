output "state_bucket_name" {
  description = "Name of the remote state S3 bucket."
  value       = aws_s3_bucket.state.id
}

output "state_bucket_arn" {
  description = "ARN of the remote state S3 bucket."
  value       = aws_s3_bucket.state.arn
}

output "dynamodb_lock_table_name" {
  description = "Name of the optional DynamoDB lock table."
  value       = aws_dynamodb_table.locks.name
}

output "dynamodb_lock_table_arn" {
  description = "ARN of the optional DynamoDB lock table."
  value       = aws_dynamodb_table.locks.arn
}

output "backend_hcl_snippet_s3_native" {
  description = "Preferred modern backend configuration using native S3 state locking (Terraform >= 1.10)."
  value       = <<-EOT
    bucket       = "${aws_s3_bucket.state.id}"
    key          = "environments/${var.environment}/terraform.tfstate"
    region       = "${var.aws_region}"
    encrypt      = true
    use_lockfile = true
  EOT
}

output "backend_hcl_snippet_dynamodb_legacy" {
  description = "Legacy backend configuration using DynamoDB table state locking."
  value       = <<-EOT
    bucket         = "${aws_s3_bucket.state.id}"
    key            = "environments/${var.environment}/terraform.tfstate"
    region         = "${var.aws_region}"
    dynamodb_table = "${aws_dynamodb_table.locks.name}"
    encrypt        = true
  EOT
}
