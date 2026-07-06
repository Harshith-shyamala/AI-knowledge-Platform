# Enterprise AI Knowledge Platform Case Study

## Summary

Enterprise AI Knowledge Platform is a production-shaped, multi-tenant RAG and
agent platform for secure enterprise knowledge workflows. It supports document
upload, indexing, hybrid retrieval, grounded chat, agent orchestration,
evaluation, observability, Streamlit demo UI, Kubernetes deployment, and AWS
Terraform scaffolding.

## Problem

Enterprise AI systems need more than a chat box. They need secure tenancy,
grounded answers, citations, role-based access control, evaluation, observability,
deployment discipline, and operational runbooks.

## Architecture

The backend follows clean architecture:

- Presentation: FastAPI routes and Streamlit UI
- Application: use cases, services, policies, retrieval, agents, evaluation
- Domain: tenant entities and knowledge objects
- Infrastructure: SQLAlchemy repositories, local storage, Docker, Kubernetes,
  Terraform

Core patterns:

- repository pattern
- unit of work
- dependency inversion
- provider abstractions
- tenant-scoped queries
- deterministic local AI gateways for repeatable tests

## What I Built

- FastAPI application factory, settings, logging, request IDs, error envelope
- SQLAlchemy persistence and Alembic migrations
- organization/workspace tenancy
- JWT authentication and RBAC
- secure upload and document versioning
- text extraction, chunking, embeddings, and indexing
- hybrid lexical/vector search
- grounded chat with citations and conversation history
- deterministic graph-shaped agent workflow
- evaluation framework for groundedness, faithfulness, answer relevance, and
  context recall
- Prometheus-style metrics endpoint
- Streamlit MVP console
- Kubernetes manifests and migration job
- AWS Terraform scaffold for VPC, ECR, S3, RDS, Secrets Manager, EKS, IAM
- production runbook and deployment validation

## Results

- 34 backend tests passing
- strict MyPy passing
- Ruff passing
- Alembic migrations validate from scratch
- Docker Compose config validates
- Kustomize renders successfully
- Terraform AWS scaffold validates locally
- Streamlit UI serves locally
- upload, index, search, chat, agent, evaluation, and metrics flows demo end to end

## Security Posture

- tenant-scoped repositories and use cases
- JWT auth and role-based permissions
- upload extension and MIME validation
- citation storage for answer auditability
- secrets separated from config in Kubernetes and Terraform
- production runbook covers rollout, rollback, migration, secrets, and incidents

## Tradeoffs

- deterministic local embeddings and answer generation keep tests stable, but
  production would use external model providers behind the existing interfaces
- local storage is used for the MVP, while S3 is represented in AWS Terraform
- synchronous indexing/evaluation keeps the demo simple; production should move
  those workloads to queue workers
- AWS Terraform is a scaffold and should add remote state, ingress, WAF, secret
  injection, cost controls, and managed observability before real production use

## Interview Talking Point

I built this as if I were joining an enterprise AI platform team: start with
tenant boundaries and use-case architecture, then add AI workflows, then add
evaluation and operations. The result is not just a RAG demo; it is a deployable
system shape with security, observability, and cloud infrastructure in mind.
