output "secret_arn" {
  description = "ARN of the Secrets Manager secret storing application credentials."
  value       = aws_secretsmanager_secret.app_secrets.arn
}

output "secret_name" {
  description = "Name of the Secrets Manager secret."
  value       = aws_secretsmanager_secret.app_secrets.name
}

output "secret_version_id" {
  description = "Version ID of the secret string payload."
  value       = aws_secretsmanager_secret_version.app_secrets.version_id
}
