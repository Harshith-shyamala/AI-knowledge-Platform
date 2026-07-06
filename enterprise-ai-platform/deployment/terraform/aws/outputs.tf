output "aws_region" {
  description = "AWS region."
  value       = var.aws_region
}

output "cluster_name" {
  description = "EKS cluster name."
  value       = aws_eks_cluster.main.name
}

output "cluster_endpoint" {
  description = "EKS cluster endpoint."
  value       = aws_eks_cluster.main.endpoint
}

output "ecr_repository_url" {
  description = "ECR repository URL for the API image."
  value       = aws_ecr_repository.api.repository_url
}

output "api_image" {
  description = "Full API image reference for Kubernetes kustomization."
  value       = "${aws_ecr_repository.api.repository_url}:${var.api_image_tag}"
}

output "documents_bucket_name" {
  description = "S3 bucket for document storage."
  value       = aws_s3_bucket.documents.bucket
}

output "api_secret_arn" {
  description = "Secrets Manager secret ARN for API runtime secrets."
  value       = aws_secretsmanager_secret.api.arn
}

output "database_endpoint" {
  description = "RDS PostgreSQL endpoint."
  value       = aws_db_instance.postgres.address
}

output "kubectl_update_command" {
  description = "Command to configure kubectl for this EKS cluster."
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${aws_eks_cluster.main.name}"
}
