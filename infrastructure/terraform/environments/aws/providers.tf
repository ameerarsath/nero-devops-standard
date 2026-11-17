provider "aws" {
  region              = var.aws_region
  allowed_account_ids = var.aws_account_id != "" ? [var.aws_account_id] : null

  dynamic "assume_role" {
    for_each = var.role_arn != "" ? [var.role_arn] : []
    content {
      role_arn     = assume_role.value
      session_name = "EnterpriseDeliveryPlatform-${var.environment}"
    }
  }

  default_tags {
    tags = merge(var.tags, {
      Project     = var.name_prefix
      Environment = var.environment
      ManagedBy   = "EnterpriseUniversalPlatform"
    })
  }
}
