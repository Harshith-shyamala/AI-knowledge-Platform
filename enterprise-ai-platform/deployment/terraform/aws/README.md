# AWS Terraform Deployment

This folder contains a concrete AWS infrastructure scaffold for EAKP.

## Resources

- VPC with public and private subnets across two availability zones
- NAT gateway for private subnet egress
- ECR repository for the API image
- S3 bucket for document storage
- RDS PostgreSQL instance
- Secrets Manager secret for API runtime secrets
- EKS cluster and managed node group
- IAM roles and policies for cluster, nodes, ECR, S3, and secrets access

## Validate

Terraform is not required for local app development. When Terraform is installed:

```bash
cd deployment/terraform/aws
terraform init -backend=false
terraform validate
```

## Deploy Outline

1. Copy `terraform.tfvars.example` to `terraform.tfvars`.
2. Replace `database_password` and `jwt_secret_key`.
3. Run `terraform init`.
4. Run `terraform plan`.
5. Run `terraform apply`.
6. Build and push the API image to the `ecr_repository_url` output.
7. Update `deployment/kubernetes/kustomization.yaml` with the `api_image` output.
8. Configure kubectl using the `kubectl_update_command` output.
9. Apply the Kubernetes bundle.

## Notes

This scaffold is suitable for portfolio and development environments. Before a
real production launch, add remote Terraform state, provider-level policy
controls, private-only cluster access, encrypted secret delivery into
Kubernetes, WAF/ingress, backup restore testing, and cost controls.
