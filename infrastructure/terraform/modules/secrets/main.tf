locals {
  actual_secret_name = var.secret_name != "" ? var.secret_name : "billing-${var.environment}/app-secrets"
}

resource "aws_secretsmanager_secret" "app_secrets" {
  name                    = local.actual_secret_name
  description             = "Application secrets for ${var.name_prefix}-${var.environment}"
  recovery_window_in_days = var.environment == "prod" ? 30 : 0

  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "app_secrets" {
  secret_id = aws_secretsmanager_secret.app_secrets.id
  secret_string = jsonencode({
    environment                = var.environment
    aws_account_id             = var.aws_account_id
    "spring.datasource.url"    = "jdbc:postgresql://${var.db_endpoint}/${var.db_name}"
    "spring.datasource.username" = var.db_username
    "spring.datasource.password" = var.db_password
    "jwt.secret"               = var.jwt_secret
    "jwt.expiration"           = var.jwt_expiration
    "app.frontend.url"         = var.frontend_url
    "app.backend.url"          = var.backend_url
    "app.invoice.base-url"     = var.invoice_base_url != "" ? var.invoice_base_url : "${var.frontend_url}/invoice"
    engine                     = "postgres"
    host                       = var.db_endpoint
    port                       = 5432
    username                   = var.db_username
    password                   = var.db_password
    database                   = var.db_name
  })
}
