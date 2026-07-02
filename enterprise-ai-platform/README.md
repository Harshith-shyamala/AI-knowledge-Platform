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

## Local Demo

Run the FastAPI backend:

```bash
cd backend
. .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Run the Streamlit console:

```bash
. backend/.venv/bin/activate
pip install -r frontend/requirements.txt
streamlit run frontend/app.py
```

- API docs: `http://127.0.0.1:8000/docs`
- Streamlit UI: `http://127.0.0.1:8501`

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

Phase 0 through Phase 13 are complete with persistence, tenancy, authentication, RBAC, secure document upload, document indexing, hybrid retrieval, grounded RAG chat, agent orchestration, evaluation, observability, a Streamlit MVP UI, production deployment scaffolding, performance tooling, security review, and portfolio polish.

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
- tenant-scoped hybrid search
- lexical and vector scoring
- score thresholding for noisy vector-only matches
- citation-ready search results with document, version, and chunk IDs
- chat, message, and citation persistence
- grounded chat API over tenant-scoped retrieval
- deterministic local answer generator behind an LLM gateway abstraction
- conversation history and transcript APIs
- deterministic agent workflow for planning, tool use, evidence inspection, reflection, and answer generation
- agent run API with traceable steps, prompt version, workflow version, and citations
- tenant-authorized agent runs over the same retrieval boundary as search and chat
- evaluation runner over golden question examples
- heuristic groundedness, faithfulness, answer relevance, and context recall evaluators
- aggregate evaluation scores with evaluator versions and thresholds
- evaluation metrics catalog API
- Prometheus-style metrics endpoint
- request count, latency sum, and latency max metrics
- low-cardinality route-template metric labels
- metrics middleware integrated with the FastAPI app factory
- Streamlit MVP console under `frontend/`
- login and registration workflow
- organization and workspace context management
- document upload, document listing, and indexing workflow
- search, chat, agent, evaluation, and metrics views
- Kubernetes manifests for namespace, config, secrets, API deployment, service, migration job, HPA, and demo Postgres
- provider-neutral Terraform scaffold for deployment inputs, naming, and outputs
- AWS Terraform scaffold for VPC, ECR, S3, RDS PostgreSQL, Secrets Manager, EKS, node groups, and IAM
- production runbook for releases, migrations, smoke checks, rollback, and incidents
- deployment validation script and CI-friendly deployment scaffold test
- API load-test script for search, chat, agent, and evaluation workflows
- security review covering tenant isolation, prompt injection, upload security, auth, secrets, and infrastructure
- prompt-injection resilience test for citation-preserving agent behavior
- portfolio case study, demo script, and interview guide
- portfolio validation script and CI-friendly portfolio asset test

## Future Upgrades

- replace deterministic local model gateways with OpenAI or Azure AI adapters
- move indexing and evaluation to queue workers
- add OpenTelemetry traces and Grafana dashboards
- add remote Terraform state and encrypted secret delivery
- add full prompt-injection fixture suite and container/dependency scans
- add React/Next.js production UI

Suggested commit message:

```text
docs: add final portfolio case study and demo guide
```
