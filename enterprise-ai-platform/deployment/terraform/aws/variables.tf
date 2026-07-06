variable "aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used in resource names."
  type        = string
  default     = "enterprise-ai-platform"
}

variable "environment" {
  description = "Environment name such as dev, staging, or prod."
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.40.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones for public/private subnets."
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "database_name" {
  description = "PostgreSQL database name."
  type        = string
  default     = "eakp"
}

variable "database_username" {
  description = "PostgreSQL master username."
  type        = string
  default     = "eakp"
}

variable "database_password" {
  description = "PostgreSQL master password. Use a real secret manager for production."
  type        = string
  sensitive   = true
}

variable "jwt_secret_key" {
  description = "JWT signing secret for the API."
  type        = string
  sensitive   = true
}

variable "api_image_tag" {
  description = "Initial API image tag to deploy from ECR."
  type        = string
  default     = "latest"
}

variable "eks_cluster_version" {
  description = "EKS Kubernetes version."
  type        = string
  default     = "1.30"
}

variable "node_instance_types" {
  description = "EC2 instance types for the EKS managed node group."
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_desired_size" {
  description = "Desired EKS node count."
  type        = number
  default     = 2
}

variable "node_min_size" {
  description = "Minimum EKS node count."
  type        = number
  default     = 1
}

variable "node_max_size" {
  description = "Maximum EKS node count."
  type        = number
  default     = 4
}

variable "allowed_database_cidrs" {
  description = "CIDR blocks allowed to reach RDS. Keep empty to allow only EKS nodes."
  type        = list(string)
  default     = []
}
