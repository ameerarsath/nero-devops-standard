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
  bucket_name = "${local.resource_prefix}-data-${random_id.bucket_suffix.hex}"
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
  source              = "../../modules/rds_postgres"
  db_identifier       = "${local.resource_prefix}-db"
  db_name             = var.db_name
  username            = var.db_username
  password            = var.db_password
  instance_class      = var.db_instance_class
  allocated_storage   = var.db_allocated_storage
  publicly_accessible = true
  skip_final_snapshot = true
  tags                = local.common_tags
}

module "frontend_website" {
  source      = "../../modules/s3_website"
  bucket_name = "${local.resource_prefix}-frontend-${random_id.bucket_suffix.hex}"
  tags        = local.common_tags
}

module "backend_ecs" {
  source         = "../../modules/ecs_backend"
  cluster_name   = "${local.resource_prefix}-cluster"
  task_family    = "${local.resource_prefix}-backend"
  service_name   = "${local.resource_prefix}-backend-service"
  image          = var.backend_image
  desired_count  = 1
  container_port = 8082
  host_port      = var.ecs_host_port

  environment_variables = [
    {
      name  = "SPRING_DATASOURCE_URL"
      value = "jdbc:postgresql://${module.rds_postgres.db_endpoint}/${var.db_name}"
    },
    {
      name  = "SPRING_DATASOURCE_USERNAME"
      value = var.db_username
    },
    {
      name  = "SPRING_DATASOURCE_PASSWORD"
      value = var.db_password
    },
    {
      name  = "SPRING_PROFILES_ACTIVE"
      value = var.environment
    }
  ]

  tags = local.common_tags
}

module "app_secrets" {
  source         = "../../modules/secrets"
  name_prefix    = var.name_prefix
  environment    = var.environment
  secret_name    = "billing-qa/app-secrets"
  aws_account_id = var.aws_account_id
  db_username    = var.db_username
  db_password    = var.db_password
  db_name        = var.db_name
  db_endpoint    = module.rds_postgres.db_endpoint
  jwt_secret     = var.jwt_secret
  jwt_expiration = var.jwt_expiration
  frontend_url   = var.frontend_url
  backend_url    = var.backend_url
  tags           = local.common_tags
}
