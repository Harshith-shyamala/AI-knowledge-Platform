# Deployment and Scaling Strategy

## Local Development

Milestone 1 should support local development with:

- FastAPI service
- PostgreSQL with pgvector
- Redis
- worker process
- optional object storage emulator such as MinIO
- Prometheus and Grafana in later milestones

```text
docker compose up
  |
  +-- api
  +-- postgres
  +-- redis
  +-- worker
  +-- minio
```

## Production Deployment

```text
Cloud DNS
  |
  v
Cloudflare / WAF
  |
  v
Cloud Load Balancer
  |
  v
Ingress Controller
  |
  +-- FastAPI API Pods
  +-- Worker Pods
  +-- Streamlit MVP UI Pod
  |
  +-- Managed PostgreSQL + pgvector
  +-- Managed Redis
  +-- Object Storage
  +-- Secrets Manager
  +-- Observability Stack
```

## Kubernetes Workloads

Recommended workloads:

- `api-deployment`: stateless FastAPI pods
- `worker-deployment`: async ingestion and evaluation workers
- `scheduler-deployment`: recurring jobs, evaluation runs, cleanup
- `streamlit-deployment`: MVP UI
- `migration-job`: Alembic migrations

## Scaling Model

### API Service

Scale horizontally by CPU, request latency, and concurrent connections. API pods should remain stateless.

### Workers

Scale by queue depth and job latency. Use separate queues for:

- document extraction
- embedding
- evaluation
- notifications

This prevents expensive embedding workloads from starving short operational tasks.

### Database

Start with managed PostgreSQL. Add:

- read replicas for dashboards and analytics
- connection pooling with PgBouncer
- partitioning for high-volume tables such as audit logs and usage metrics
- vector index tuning as corpus size grows

### Object Storage

Use local filesystem only for the earliest milestone. Move to S3-compatible storage before multi-user demos.

## Reliability

Required controls:

- readiness checks for database, Redis, and queue dependencies
- retry with exponential backoff for provider calls
- dead-letter queues for failed async jobs
- idempotency keys for upload and ingestion tasks
- graceful shutdown for workers
- migration rollback strategy

## Observability Deployment

```text
FastAPI + Workers
  |
  +-- Prometheus metrics
  +-- OpenTelemetry traces
  +-- structured JSON logs
  |
  v
Prometheus -> Grafana
OpenTelemetry Collector -> Jaeger
Logs -> Loki
```

## Cost Controls

- cache embeddings by content hash
- track token usage by organization, workspace, user, agent, and model
- enforce tenant-level budgets
- use cheaper models for evaluation and summarization when acceptable
- batch embeddings where provider limits allow
- support model routing by use case

## Cloud Strategy

The architecture should be cloud-portable, but the first polished deployment path should choose one primary cloud to avoid shallow multi-cloud work.

Recommended first cloud: AWS.

Reasoning:

- S3 maps cleanly to object storage
- RDS PostgreSQL supports pgvector patterns
- ElastiCache supports Redis
- EKS maps to Kubernetes readiness
- IAM and Secrets Manager are familiar to hiring teams

Azure and GCP compatibility should be documented through adapter boundaries, not implemented prematurely.

## Terraform Scope

Phase 11 Terraform should provision:

- VPC and subnets
- Kubernetes cluster or container service
- managed PostgreSQL
- Redis
- object storage bucket
- secrets manager entries
- monitoring namespace
- IAM roles

Do not put application secrets directly in Terraform state.

