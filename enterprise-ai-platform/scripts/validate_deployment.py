from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


REQUIRED_FILES = [
    "deployment/docker/Dockerfile.api",
    "deployment/docker/docker-compose.yml",
    "deployment/kubernetes/namespace.yaml",
    "deployment/kubernetes/configmap.yaml",
    "deployment/kubernetes/secret.example.yaml",
    "deployment/kubernetes/serviceaccount.yaml",
    "deployment/kubernetes/api-deployment.yaml",
    "deployment/kubernetes/api-service.yaml",
    "deployment/kubernetes/migration-job.yaml",
    "deployment/kubernetes/hpa.yaml",
    "deployment/kubernetes/postgres-demo.yaml",
    "deployment/kubernetes/kustomization.yaml",
    "deployment/terraform/versions.tf",
    "deployment/terraform/variables.tf",
    "deployment/terraform/main.tf",
    "deployment/terraform/outputs.tf",
    "deployment/terraform/aws/versions.tf",
    "deployment/terraform/aws/variables.tf",
    "deployment/terraform/aws/locals.tf",
    "deployment/terraform/aws/network.tf",
    "deployment/terraform/aws/security.tf",
    "deployment/terraform/aws/ecr.tf",
    "deployment/terraform/aws/storage.tf",
    "deployment/terraform/aws/database.tf",
    "deployment/terraform/aws/secrets.tf",
    "deployment/terraform/aws/iam.tf",
    "deployment/terraform/aws/eks.tf",
    "deployment/terraform/aws/outputs.tf",
    "deployment/terraform/aws/terraform.tfvars.example",
    "deployment/terraform/aws/README.md",
    "docs/operations/production-runbook.md",
]

REQUIRED_KUSTOMIZE_RESOURCES = [
    "namespace.yaml",
    "configmap.yaml",
    "serviceaccount.yaml",
    "secret.example.yaml",
    "api-deployment.yaml",
    "api-service.yaml",
    "migration-job.yaml",
    "hpa.yaml",
    "postgres-demo.yaml",
]


def main() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        raise SystemExit(f"Missing deployment files: {', '.join(missing)}")

    dockerfile = _read("deployment/docker/Dockerfile.api")
    _require("COPY backend/alembic ./alembic", dockerfile, "Dockerfile includes Alembic")
    _require(
        "COPY backend/alembic.ini ./alembic.ini",
        dockerfile,
        "Dockerfile includes alembic.ini",
    )

    deployment = _read("deployment/kubernetes/api-deployment.yaml")
    _require("readinessProbe:", deployment, "API deployment has readiness probe")
    _require("livenessProbe:", deployment, "API deployment has liveness probe")
    _require("resources:", deployment, "API deployment has resources")
    _require("allowPrivilegeEscalation: false", deployment, "API deployment hardens container")

    migration = _read("deployment/kubernetes/migration-job.yaml")
    _require("- alembic", migration, "Migration job runs Alembic")
    _require("- upgrade", migration, "Migration job upgrades")
    _require("- head", migration, "Migration job targets head")

    kustomization = _read("deployment/kubernetes/kustomization.yaml")
    for resource in REQUIRED_KUSTOMIZE_RESOURCES:
        _require(f"- {resource}", kustomization, f"kustomization references {resource}")

    terraform = "\n".join(
        [
            _read("deployment/terraform/versions.tf"),
            _read("deployment/terraform/variables.tf"),
            _read("deployment/terraform/main.tf"),
            _read("deployment/terraform/outputs.tf"),
        ]
    )
    _require('required_version = ">= 1.6.0"', terraform, "Terraform version is pinned")
    _require('variable "database_url"', terraform, "Terraform declares database URL")
    _require('variable "jwt_secret_key"', terraform, "Terraform declares JWT secret")

    aws_terraform = "\n".join(
        [
            _read("deployment/terraform/aws/versions.tf"),
            _read("deployment/terraform/aws/variables.tf"),
            _read("deployment/terraform/aws/network.tf"),
            _read("deployment/terraform/aws/ecr.tf"),
            _read("deployment/terraform/aws/storage.tf"),
            _read("deployment/terraform/aws/database.tf"),
            _read("deployment/terraform/aws/secrets.tf"),
            _read("deployment/terraform/aws/iam.tf"),
            _read("deployment/terraform/aws/eks.tf"),
            _read("deployment/terraform/aws/outputs.tf"),
        ]
    )
    _require('source  = "hashicorp/aws"', aws_terraform, "AWS provider is declared")
    _require('resource "aws_vpc" "main"', aws_terraform, "AWS VPC is declared")
    _require('resource "aws_ecr_repository" "api"', aws_terraform, "AWS ECR is declared")
    _require('resource "aws_s3_bucket" "documents"', aws_terraform, "AWS S3 is declared")
    _require('resource "aws_db_instance" "postgres"', aws_terraform, "AWS RDS is declared")
    _require(
        'resource "aws_secretsmanager_secret" "api"',
        aws_terraform,
        "AWS Secrets Manager is declared",
    )
    _require('resource "aws_eks_cluster" "main"', aws_terraform, "AWS EKS is declared")
    _require('resource "aws_eks_node_group" "main"', aws_terraform, "AWS nodes are declared")

    print("Deployment scaffold validation passed.")


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _require(needle: str, haystack: str, label: str) -> None:
    if needle not in haystack:
        raise SystemExit(f"Deployment validation failed: {label}")


if __name__ == "__main__":
    main()
