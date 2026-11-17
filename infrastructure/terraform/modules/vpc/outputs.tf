output "vpc_id" {
  description = "ID of the dedicated VPC."
  value       = aws_vpc.this.id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets."
  value       = aws_subnet.public[*].id
}

output "application_subnet_ids" {
  description = "IDs of the private application subnets."
  value       = aws_subnet.application[*].id
}

output "database_subnet_ids" {
  description = "IDs of the private database subnets."
  value       = aws_subnet.database[*].id
}

output "db_subnet_group_name" {
  description = "Name of the RDS DB Subnet Group."
  value       = aws_db_subnet_group.this.name
}

output "alb_security_group_id" {
  description = "ID of the ALB security group."
  value       = aws_security_group.alb.id
}

output "ecs_security_group_id" {
  description = "ID of the ECS security group."
  value       = aws_security_group.ecs.id
}

output "rds_security_group_id" {
  description = "ID of the RDS security group."
  value       = aws_security_group.rds.id
}
