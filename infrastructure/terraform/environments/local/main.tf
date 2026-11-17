locals {
  resource_prefix = "${var.name_prefix}-${var.environment}"
  common_tags = merge(var.tags, {
    Project     = var.name_prefix
    Environment = var.environment
    ManagedBy   = "Terraform"
  })
}

resource "random_id" "bucket_suffix" {
  byte_length = 3
}

module "app_bucket" {
  source      = "../../modules/s3_bucket"
  bucket_name = "${local.resource_prefix}-${random_id.bucket_suffix.hex}"
  tags        = local.common_tags
}

module "jobs_queue" {
  source     = "../../modules/sqs_queue"
  queue_name = "${local.resource_prefix}-jobs"
  tags       = local.common_tags
}

module "app_table" {
  source     = "../../modules/dynamodb_table"
  table_name = "${local.resource_prefix}-items"
  hash_key   = "id"
  tags       = local.common_tags
}

module "rds_postgres" {
  source        = "../../modules/rds_postgres"
  db_identifier = "${local.resource_prefix}-db"
  db_name       = "hotel_billing"
  username      = "postgres"
  password      = "postgres"
  tags          = local.common_tags
}

module "frontend_website" {
  source      = "../../modules/s3_website"
  bucket_name = "${local.resource_prefix}-frontend-${random_id.bucket_suffix.hex}"
  tags        = local.common_tags
}

module "backend_ecs" {
  source       = "../../modules/ecs_backend"
  cluster_name = "${local.resource_prefix}-cluster"
  task_family  = "${local.resource_prefix}-backend"
  service_name = "${local.resource_prefix}-backend-service"
  image        = "billing-backend:local"
  host_port    = 8083

  environment_variables = [
    {
      name  = "SPRING_DATASOURCE_URL"
      value = "jdbc:postgresql://${module.rds_postgres.db_endpoint}/hotel_billing"
    },
    {
      name  = "SPRING_DATASOURCE_USERNAME"
      value = "postgres"
    },
    {
      name  = "SPRING_DATASOURCE_PASSWORD"
      value = "postgres"
    }
  ]

  tags = local.common_tags
}
