# Terraform Scaffold

This folder defines the cloud deployment contract for EAKP.

The current phase keeps Terraform provider-neutral so it can validate locally and be
adapted to AWS, Azure, GCP, or an internal platform without rewriting the app.

For a concrete AWS implementation, see [`aws/`](aws/).

## Expected Production Resources

- managed PostgreSQL with pgvector support
- container registry repository
- Kubernetes cluster or managed app platform
- secret manager entries for `EAKP_DATABASE_URL` and `EAKP_JWT_SECRET_KEY`
- object storage for document uploads
- observability workspace for metrics, logs, and traces

## AWS Implementation

The `aws/` folder includes Terraform for:

- VPC, public/private subnets, internet gateway, and NAT gateway
- ECR repository
- S3 document bucket
- RDS PostgreSQL
- Secrets Manager
- EKS cluster and managed node group
- IAM roles and policies

## Validate

```bash
terraform init -backend=false
terraform validate
```

Copy `terraform.tfvars.example` to `terraform.tfvars` and replace secrets for a
real environment. Do not commit real secret values.
