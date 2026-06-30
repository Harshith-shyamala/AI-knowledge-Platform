# Enterprise AI Knowledge Platform

Enterprise AI Knowledge Platform (EAKP) is a production-grade portfolio project blueprint for a secure, multi-tenant knowledge intelligence platform. It is designed to demonstrate enterprise AI engineering across document ingestion, RAG, hybrid retrieval, agent orchestration, evaluation, observability, and cloud-ready deployment.

This repository area is intentionally starting with Phase 0: architecture, contracts, roadmap, and operating model. The implementation should proceed milestone by milestone so each phase remains independently runnable, reviewable, and defensible in a senior engineering interview.

## Product Vision

EAKP enables organizations to upload enterprise knowledge and ask natural language questions over it with grounded answers, citations, access controls, and operational telemetry.

The platform is modeled after internal enterprise AI systems such as Microsoft Copilot, Glean, Notion AI, Atlassian Intelligence, and ChatGPT Enterprise, while keeping implementation choices explicit and portfolio-friendly.

## Audience

- Recruiters: polished repository, clear README, professional roadmap, demo-ready story.
- Hiring managers: deployable architecture, clear milestones, cloud and security posture.
- Senior engineers: clean architecture, SOLID boundaries, tests, dependency inversion.
- ML engineers: RAG, hybrid retrieval, reranking, evaluation, prompt/version management.
- DevOps engineers: Docker, Kubernetes readiness, Terraform readiness, CI/CD, monitoring.

## Phase 0 Deliverables

- [Architecture overview](docs/architecture/architecture.md)
- [Data model and tenancy design](docs/architecture/data-model.md)
- [API contract](docs/api/api-contract.md)
- [Sequence diagrams](docs/architecture/sequences.md)
- [Deployment and scaling strategy](docs/operations/deployment-scaling.md)
- [Security architecture](docs/security/security-architecture.md)
- [Milestone roadmap](docs/roadmap/milestones.md)

## Target Technology Stack

- Python 3.12+
- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- pgvector
- Redis
- Celery or Dramatiq
- LangGraph for agent orchestration
- OpenAI embeddings and LLMs behind provider abstractions
- Streamlit MVP UI, React/Next.js later
- Docker, Docker Compose, Kubernetes, Terraform
- Prometheus, Grafana, OpenTelemetry, Jaeger, Loki
- Pytest, Ruff, MyPy, pre-commit, GitHub Actions

## Clean Architecture Boundary

```text
Presentation Layer
  FastAPI routers, Streamlit UI, API schemas

Application Layer
  Use cases, commands, queries, orchestration, policies

Domain Layer
  Entities, value objects, domain services, events

Infrastructure Layer
  SQLAlchemy, pgvector, Redis, object storage, LLM providers, queues
```

Business logic must live in the application and domain layers, not in API routes, ORM models, or UI components.

## Initial Project Shape

```text
enterprise-ai-platform/
  backend/
    app/
    tests/
  frontend/
  docs/
    api/
    architecture/
    operations/
    roadmap/
    security/
  deployment/
    docker/
    kubernetes/
    terraform/
  scripts/
  .github/
    workflows/
```

## Current Implementation Status

Phase 0 through Phase 5 are complete with persistence, tenancy, authentication, RBAC, secure document upload, and document indexing under `backend/`.

Implemented Phase 1 capabilities:

- FastAPI app factory
- typed settings
- JSON structured logging
- request ID middleware
- error envelope
- health and readiness endpoints
- application service container
- tests
- Dockerfile and Docker Compose
- GitHub Actions CI workflow
- SQLAlchemy persistence foundation
- Alembic migration scaffold
- organization and workspace tenancy APIs
- tenant-scoped workspace repository behavior
- PostgreSQL + pgvector Docker Compose service
- JWT registration, login, refresh, and current-user endpoints
- password hashing with PBKDF2
- organization memberships and RBAC permission checks
- cross-tenant authorization tests
- secure document upload validation
- local document storage adapter
- document metadata and versioning
- document upload/list/get/version APIs
- upload authorization and cross-tenant document tests
- text extraction for text-like uploads
- text cleaning and fixed-window chunking
- deterministic embedding gateway
- chunk and embedding persistence
- document indexing and chunk listing APIs



Suggested commit message:

```text
feat: add document indexing pipeline
```
