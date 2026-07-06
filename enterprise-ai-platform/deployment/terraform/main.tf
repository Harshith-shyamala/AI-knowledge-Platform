locals {
  name_prefix = "${var.project_name}-${var.environment}"
  labels = {
    project     = var.project_name
    environment = var.environment
    managed_by  = "terraform"
  }
  kubernetes_namespace = var.namespace
  api_service_name     = "eakp-api"
}

# Provider-specific resources are intentionally left as the next implementation step.
# Recommended production resources:
# - managed PostgreSQL with pgvector support
# - container registry repository
# - Kubernetes cluster or app platform
# - secret manager entries for database URL and JWT secret
# - object storage bucket for uploaded documents
# - observability workspace for logs, metrics, and traces
