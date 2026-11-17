output "environment" {
  description = "The active environment name."
  value       = var.environment
}

output "aws_account_id" {
  description = "The dedicated AWS account ID for this environment."
  value       = var.aws_account_id
}

output "floci_endpoint" {
  description = "Floci endpoint used."
  value       = var.floci_endpoint
}

output "app_bucket_name" {
  description = "S3 application data bucket name."
  value       = module.app_bucket.bucket_name
}

output "jobs_queue_url" {
  description = "SQS job queue URL."
  value       = module.jobs_queue.queue_url
}

output "dynamodb_table_name" {
  description = "DynamoDB items table name."
  value       = module.app_table.table_name
}

output "rds_endpoint" {
  description = "PostgreSQL RDS connection endpoint."
  value       = module.rds_postgres.db_endpoint
}

output "frontend_website_endpoint" {
  description = "Frontend S3 website hosting endpoint."
  value       = module.frontend_website.website_endpoint
}

output "ecs_cluster_name" {
  description = "ECS cluster name hosting backend tasks."
  value       = module.backend_ecs.cluster_name
}

output "ecs_service_name" {
  description = "ECS service name running the backend."
  value       = module.backend_ecs.service_name
}

output "secret_arn" {
  description = "Secrets Manager secret ARN for this environment."
  value       = module.app_secrets.secret_arn
}

output "secret_name" {
  description = "Secrets Manager secret name."
  value       = module.app_secrets.secret_name
}
