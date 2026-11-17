resource "aws_db_instance" "this" {
  identifier          = var.db_identifier
  engine              = "postgres"
  engine_version      = var.engine_version
  instance_class      = var.instance_class
  allocated_storage   = var.allocated_storage
  db_name             = var.db_name
  username            = var.username
  password            = var.password
  skip_final_snapshot = var.skip_final_snapshot
  publicly_accessible = var.publicly_accessible

  # Hardened Networking & Isolation
  db_subnet_group_name   = var.db_subnet_group_name
  vpc_security_group_ids = var.vpc_security_group_ids

  # Reliability & Backup Protection
  deletion_protection     = var.deletion_protection
  multi_az                = var.multi_az
  backup_retention_period = var.backup_retention_period
  backup_window           = var.backup_window
  maintenance_window      = var.maintenance_window

  tags = var.tags
}
