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

Phase 0 through Phase 2 are complete. The platform now has a production-oriented backend foundation, database persistence, tenant-aware domain modeling, JWT authentication, and an RBAC-ready authorization boundary.

These first phases intentionally focus on the engineering foundation before adding RAG features. In an enterprise AI platform, document intelligence is only useful if the underlying system has clear service boundaries, reliable persistence, secure identity, tenant isolation, and testable authorization behavior.

### Phase 1: Backend Foundation

Phase 1 establishes the backend architecture for a maintainable FastAPI service that can support future document ingestion, retrieval, RAG, evaluation, and agent workflows.

#### What Was Built

- FastAPI app factory
- typed configuration and environment-based settings
- JSON structured logging with request correlation
- request ID middleware for traceability
- standardized error envelope
- health and readiness endpoints
- application service container for dependency injection
- SQLAlchemy persistence foundation
- Alembic migration scaffold
- PostgreSQL + pgvector Docker Compose service
- Dockerfile and Docker Compose local runtime
- GitHub Actions CI workflow
- test coverage for application startup and health checks

#### Engineering Capabilities Demonstrated

- Clean application bootstrapping through an app factory instead of global framework state
- Centralized configuration so local, CI, and production environments can be managed consistently
- Structured logs and request IDs to make API behavior traceable across services
- Standardized error responses for predictable client and frontend integration
- Dependency-injection-friendly service container to avoid hard-coding infrastructure dependencies
- Database and migration foundation ready for tenant, document, chunk, embedding, conversation, and audit entities
- Dockerized local development environment with PostgreSQL and pgvector ready for future vector search
- CI workflow foundation for repeatable validation before merging changes

#### Why It Matters

This phase turns the project from a script or demo into the beginning of a real backend platform. The focus is on operational readiness: configuration, observability, health checks, migrations, dependency boundaries, and repeatable local development.

#### Validation

- Health endpoint tests verify that the app starts correctly
- Readiness behavior validates infrastructure connectivity boundaries
- Application factory tests protect startup wiring
- CI is prepared to run automated checks as the codebase grows

### Phase 2: Identity, Tenancy, and RBAC

Phase 2 adds the identity and access-control foundation required for a secure, multi-tenant enterprise AI platform.

#### What Was Built

- organization and workspace tenancy APIs
- tenant-scoped workspace repository behavior
- JWT registration, login, refresh, and current-user endpoints
- password hashing with PBKDF2
- user, organization, and membership persistence models
- role-based access control permission checks
- cross-tenant authorization tests

#### Core Domain Model

```text
User
  belongs to Organizations through Memberships

Organization
  owns Workspaces

Workspace
  becomes the security and retrieval boundary for future documents,
  conversations, prompts, evaluations, and agents

Membership
  connects a user to an organization with a role
```

#### Security Capabilities Demonstrated

- Passwords are stored using a one-way password hashing strategy
- Login issues JWT access tokens instead of storing server-side session state
- Current-user endpoint validates token-based identity
- Organization membership controls access to tenant-owned resources
- Repository behavior is tenant scoped to prevent accidental cross-organization reads
- RBAC checks create a reusable authorization boundary for future upload, search, chat, admin, and agent actions

#### Why It Matters

Enterprise AI systems handle sensitive company knowledge. Before adding document upload or retrieval, the platform must answer a more fundamental question: who is allowed to access which organization, workspace, document, and AI capability?

Phase 2 creates the foundation for secure multi-tenancy so later RAG features can be built on top of organization and workspace boundaries instead of retrofitting security after the fact.

#### Validation

- Authentication tests cover registration, login, token refresh, and current-user behavior
- Authorization tests verify role-based permission checks
- Cross-tenant tests confirm that users cannot access resources outside their organization
- Repository tests validate tenant-scoped data access patterns

### Current Platform Foundation

After Phase 1 and Phase 2, the platform can support:

- production-style FastAPI service structure
- database-backed organizations, users, memberships, and workspaces
- JWT-based authentication flow
- RBAC-ready permission checks
- tenant-scoped repository access
- Dockerized local development with PostgreSQL and pgvector
- CI-ready backend validation

## Next Engineering Milestone

Phase 3 will introduce secure document upload and knowledge management:

- file validation and upload authorization
- local storage adapter with S3-compatible abstraction
- document metadata persistence
- document versioning
- tenant-scoped document APIs
- cross-tenant document access tests

## Future Upgrades

- replace deterministic local model gateways with OpenAI or Azure AI adapters
- move indexing and evaluation to queue workers
- add OpenTelemetry traces and Grafana dashboards
- add remote Terraform state and encrypted secret delivery
- add full prompt-injection fixture suite and container/dependency scans
- add React/Next.js production UI

Suggested commit message:

```text
docs: document phase 1 and phase 2 platform foundation
```
