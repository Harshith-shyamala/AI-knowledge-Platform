locals {
  name_prefix = "${var.project_name}-${var.environment}"
  azs         = var.availability_zones

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}
