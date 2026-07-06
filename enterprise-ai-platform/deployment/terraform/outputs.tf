output "name_prefix" {
  description = "Prefix to use for provider-specific cloud resources."
  value       = local.name_prefix
}

output "kubernetes_namespace" {
  description = "Namespace expected by the Kubernetes manifests."
  value       = local.kubernetes_namespace
}

output "api_service_name" {
  description = "Kubernetes service name for the API."
  value       = local.api_service_name
}

output "container_image" {
  description = "API image that should be deployed."
  value       = var.container_image
}
