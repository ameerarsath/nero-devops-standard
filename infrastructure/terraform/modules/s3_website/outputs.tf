output "bucket_name" {
  description = "Name of the website bucket."
  value       = aws_s3_bucket.this.id
}

output "bucket_arn" {
  description = "ARN of the website bucket."
  value       = aws_s3_bucket.this.arn
}

output "website_endpoint" {
  description = "Website endpoint."
  value       = aws_s3_bucket_website_configuration.this.website_endpoint
}

output "website_domain" {
  description = "Domain of the website endpoint."
  value       = aws_s3_bucket_website_configuration.this.website_domain
}
