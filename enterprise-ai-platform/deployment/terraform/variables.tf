variable "project_name" {
  description = "Project name used for cloud resource naming."
  type        = string
  default     = "enterprise-ai-platform"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "dev"
}

variable "container_image" {
  description = "API container image reference."
  type        = string
  default     = "ghcr.io/your-org/enterprise-ai-platform-api:latest"
}

variable "database_url" {
  description = "Managed PostgreSQL connection URL. Store as a secret in real deployments."
  type        = string
  sensitive   = true
}

variable "jwt_secret_key" {
  description = "JWT signing secret. Store in a cloud secret manager in real deployments."
  type        = string
  sensitive   = true
}

variable "namespace" {
  description = "Kubernetes namespace for the API."
  type        = string
  default     = "eakp"
}
