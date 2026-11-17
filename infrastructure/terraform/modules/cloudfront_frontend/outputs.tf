output "bucket_name" {
  description = "Name of the private frontend S3 bucket."
  value       = aws_s3_bucket.frontend.id
}

output "bucket_arn" {
  description = "ARN of the private frontend S3 bucket."
  value       = aws_s3_bucket.frontend.arn
}

output "cloudfront_distribution_id" {
  description = "ID of the CloudFront distribution."
  value       = aws_cloudfront_distribution.this.id
}

output "cloudfront_distribution_arn" {
  description = "ARN of the CloudFront distribution."
  value       = aws_cloudfront_distribution.this.arn
}

output "cloudfront_domain_name" {
  description = "Domain name of the CloudFront distribution (e.g. d1234.cloudfront.net)."
  value       = aws_cloudfront_distribution.this.domain_name
}
