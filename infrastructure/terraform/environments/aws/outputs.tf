output "vpc_id" {
  description = "ID of the sandbox VPC."
  value       = aws_vpc.this.id
}

output "public_subnets" {
  description = "IDs of the public subnets."
  value       = aws_subnet.public[*].id
}

output "alb_dns_name" {
  description = "Public DNS name of the Application Load Balancer."
  value       = aws_lb.this.dns_name
}

output "alb_arn" {
  description = "ARN of the Application Load Balancer."
  value       = aws_lb.this.arn
}

output "target_group_arn" {
  description = "ARN of the backend Target Group."
  value       = aws_lb_target_group.backend.arn
}

output "ecr_repository_url" {
  description = "Amazon ECR Repository URI for image publishing."
  value       = aws_ecr_repository.repo.repository_url
}

output "ecs_cluster_name" {
  description = "Name of the ECS Cluster."
  value       = aws_ecs_cluster.this.name
}

output "ecs_service_name" {
  description = "Name of the ECS Fargate Service."
  value       = aws_ecs_service.this.name
}

output "cloudwatch_log_group" {
  description = "CloudWatch Log Group name for container logs."
  value       = aws_cloudwatch_log_group.ecs.name
}
