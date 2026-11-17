output "s3_bucket_name" {
  description = "Created application bucket."
  value       = module.app_bucket.bucket_name
}

output "sqs_queue_url" {
  description = "Created jobs queue URL."
  value       = module.jobs_queue.queue_url
}

output "dynamodb_table_name" {
  description = "Created DynamoDB table."
  value       = module.app_table.table_name
}

output "rds_endpoint" {
  description = "RDS PostgreSQL connection endpoint."
  value       = module.rds_postgres.db_endpoint
}

output "rds_db_name" {
  description = "RDS PostgreSQL default database name."
  value       = module.rds_postgres.db_name
}

output "frontend_website_endpoint" {
  description = "Frontend S3 website hosting endpoint."
  value       = module.frontend_website.website_endpoint
}

output "frontend_bucket_name" {
  description = "Frontend S3 bucket name."
  value       = module.frontend_website.bucket_name
}

output "ecs_cluster_name" {
  description = "Backend ECS cluster name."
  value       = module.backend_ecs.cluster_name
}

output "ecs_service_name" {
  description = "Backend ECS service name."
  value       = module.backend_ecs.service_name
}
