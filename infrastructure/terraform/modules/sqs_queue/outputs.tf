output "queue_url" {
  description = "Queue URL."
  value       = aws_sqs_queue.this.url
}

output "queue_arn" {
  description = "Queue ARN."
  value       = aws_sqs_queue.this.arn
}
