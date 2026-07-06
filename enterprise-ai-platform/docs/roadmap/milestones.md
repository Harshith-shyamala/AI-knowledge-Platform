# Milestone Roadmap

## Phase 0: Architecture and Repository Foundation

Goal:

Define the architecture, boundaries, APIs, data model, deployment strategy, and development roadmap.

Deliverables:

- architecture guide
- data model guide
- API contract
- sequence diagrams
- security architecture
- deployment and scaling strategy
- milestone roadmap

Definition of done:

- documentation is specific enough to drive implementation
- folder structure exists
- next milestone is independently actionable

Resume bullet:

Built the architecture blueprint for a multi-tenant enterprise AI knowledge platform covering RAG, hybrid retrieval, LLM gateways, evaluation, security, observability, and cloud-ready deployment.

LinkedIn post:

I started a production-grade Enterprise AI Knowledge Platform portfolio project by treating architecture as the first deliverable. Phase 0 defines the tenancy model, clean architecture boundaries, RAG and evaluation flows, API contracts, security posture, and deployment strategy before writing application code.

Suggested commit:

```text
docs: define enterprise ai platform architecture and roadmap
```

## Phase 1: Backend Service Foundation

Goal:

Create an independently runnable FastAPI backend with production-grade project hygiene.

Architecture:

- FastAPI app factory
- typed configuration
- structured logging
- dependency injection container
- health checks
- exception handling
- request id middleware

Files:

- `backend/pyproject.toml`
- `backend/app/main.py`
- `backend/app/core/config.py`
- `backend/app/core/logging.py`
- `backend/app/api/health.py`
- `backend/tests/test_health.py`
- `deployment/docker/Dockerfile.api`
- `deployment/docker/docker-compose.yml`
- `.github/workflows/backend-ci.yml`

Testing:

- unit tests for settings
- API tests for liveness/readiness
- linting with Ruff
- typing with MyPy

Common bugs:

- environment variables read at import time in ways that break tests
- health checks that claim readiness before dependencies are reachable
- routes containing business logic

Interview questions:

- Why use an app factory in FastAPI?
- What is the difference between liveness and readiness?
- How do you keep framework code out of business logic?

Design decisions:

- Pydantic settings for config
- JSON logs for production
- dependency inversion from the beginning

Possible improvements:

- add OpenTelemetry middleware
- add Prometheus metrics
- add API versioning

Resume bullet:

Implemented a production-ready FastAPI foundation with typed configuration, structured logging, health checks, dependency injection, Docker support, and CI validation.

Suggested commit:

```text
feat: add fastapi backend foundation
```

## Phase 2: Persistence, Migrations, and Tenancy

Goal:

Add PostgreSQL, SQLAlchemy, Alembic, tenant-scoped repositories, and base domain entities.

Architecture:

- SQLAlchemy infrastructure models
- domain entities separate from ORM
- repository interfaces in application layer
- concrete repositories in infrastructure layer
- unit of work abstraction

Testing:

- repository integration tests
- migration smoke tests
- tenant isolation tests

Resume bullet:

Designed and implemented tenant-scoped persistence using PostgreSQL, SQLAlchemy, Alembic, repository abstractions, and unit-of-work transaction boundaries.

Suggested commit:

```text
feat: add tenant-scoped persistence layer
```

## Phase 3: Authentication and RBAC

Goal:

Implement JWT auth, user registration/login, organization membership, workspace membership, and permission checks.

Architecture:

- auth service
- password hashing
- JWT token service
- RBAC policy service
- audit logging

Testing:

- auth API tests
- permission matrix tests
- tenant isolation tests

Resume bullet:

Implemented JWT authentication and role-based access control for a multi-tenant AI knowledge platform with organization and workspace-level authorization.

Suggested commit:

```text
feat: add jwt authentication and rbac
```

## Phase 4: Document Upload and Metadata

Goal:

Support secure uploads, metadata persistence, object storage abstraction, versioning, and ingestion job creation.

Architecture:

- upload use case
- file validator
- storage port and local storage adapter
- document repository
- ingestion queue producer

Testing:

- file validation tests
- upload API tests
- document versioning tests
- duplicate hash tests

Resume bullet:

Built secure document upload and versioning workflows with validation, content hashing, metadata storage, and asynchronous ingestion job creation.

Suggested commit:

```text
feat: add document upload and versioning
```

## Phase 5: Text Extraction, Chunking, and Embeddings

Goal:

Extract text from supported files, clean content, chunk text, generate embeddings, and store vectors.

Architecture:

- extractor strategies by MIME type
- chunking strategy interface
- embedding gateway abstraction
- pgvector repository
- worker retries and job status

Testing:

- extractor fixtures
- chunk boundary tests
- embedding gateway fake provider tests
- worker integration tests

Resume bullet:

Implemented an asynchronous ingestion pipeline that extracts, cleans, chunks, embeds, and indexes enterprise documents using provider-agnostic embedding abstractions.

Suggested commit:

```text
feat: add document ingestion and embeddings pipeline
```

## Phase 6: Hybrid Retrieval and Reranking

Goal:

Implement metadata-filtered hybrid search using PostgreSQL full-text search, pgvector semantic search, candidate merging, and reranking.

Architecture:

- retrieval service
- lexical search adapter
- vector search adapter
- rank fusion
- reranker strategy
- citation builder

Testing:

- retrieval unit tests
- tenant-filter integration tests
- ranking fixture tests

Resume bullet:

Built a tenant-aware hybrid retrieval engine combining semantic vector search, lexical search, metadata filtering, rank fusion, and reranking for grounded AI responses.

Suggested commit:

```text
feat: add hybrid retrieval and reranking
```

## Phase 7: RAG Chat and Conversation Memory

Goal:

Allow users to ask questions over workspace knowledge with grounded answers, citations, streaming, and conversation history.

Architecture:

- ask question use case
- context builder
- prompt builder
- LLM gateway
- conversation repository
- SSE streaming endpoint

Testing:

- prompt construction tests
- citation tests
- fake LLM integration tests
- chat API tests

Resume bullet:

Implemented a grounded RAG chat pipeline with conversation memory, prompt versioning, citation generation, streaming responses, and provider-agnostic LLM routing.

Suggested commit:

```text
feat: add grounded rag chat pipeline
```

## Phase 8: LangGraph Agent Orchestration

Goal:

Add configurable agents with tools, memory policy, knowledge scope, and execution traces.

Current implementation:

- deterministic graph-shaped workflow
- planner step
- tenant-scoped search tool
- evidence inspection step
- grounding reflection step
- final answer generation
- API trace with prompt and workflow versions

Architecture:

- agent definition model
- internal tool interface
- LangGraph runtime adapter
- agent run repository
- trace events

Testing:

- agent policy tests
- tool authorization tests
- graph execution tests with fake tools and fake LLM

Resume bullet:

Built configurable LangGraph-based AI agents with scoped tools, knowledge access policies, execution traces, and auditable run history.

Suggested commit:

```text
feat: add configurable langgraph agents
```

## Phase 9: Evaluation Framework

Goal:

Evaluate answer faithfulness, groundedness, answer relevance, context precision, context recall, latency, usage, and cost.

Current implementation:

- synchronous evaluation run API
- golden question examples supplied in the request
- heuristic groundedness evaluator
- heuristic faithfulness evaluator
- heuristic answer relevance evaluator
- heuristic context recall evaluator
- aggregate score calculation with evaluator versions and thresholds
- evaluator catalog API

Architecture:

- evaluation queue
- evaluator interfaces
- heuristic evaluators
- LLM-as-judge adapter
- benchmark dataset runner
- evaluation dashboard API

Testing:

- evaluator unit tests
- fixture-based benchmark tests
- regression tests for known hallucination cases

Resume bullet:

Implemented an LLM evaluation framework tracking groundedness, faithfulness, answer relevance, context quality, hallucination risk, latency, token usage, and cost.

Suggested commit:

```text
feat: add rag evaluation framework
```

## Phase 10: Observability and Operations

Goal:

Add metrics, traces, dashboards, operational logs, and incident-ready health checks.

Current implementation:

- in-process metrics registry
- FastAPI metrics middleware
- Prometheus-style `/metrics` endpoint
- HTTP request count metrics
- HTTP latency sum and max metrics
- route-template labels to avoid high-cardinality UUID paths

Architecture:

- Prometheus metrics
- OpenTelemetry traces
- Grafana dashboards
- structured log correlation
- operational runbooks

Testing:

- metrics endpoint tests
- trace propagation tests
- readiness failure tests

Resume bullet:

Added production observability with Prometheus metrics, OpenTelemetry traces, Grafana dashboards, structured logs, and operational readiness checks.

Suggested commit:

```text
feat: add observability stack
```

## Phase 11: Streamlit MVP UI

Goal:

Provide a demo-ready UI for document upload, indexing status, search, chat, citations, and admin metrics.

Current implementation:

- Streamlit app in `frontend/app.py`
- API base URL and health check controls
- login and registration forms
- organization and workspace selection
- document upload, listing, and indexing controls
- search results with document, version, and chunk identifiers
- chat answer and citation view
- agent answer, trace, and citation view
- evaluation runner and evaluator catalog view
- raw Prometheus metrics view

Architecture:

- Streamlit client
- API client wrapper
- upload view
- chat view
- search view
- admin metrics view

Testing:

- API client tests
- smoke tests for Streamlit startup

Resume bullet:

Built a demo-ready Streamlit interface for enterprise document upload, indexing visibility, hybrid search, grounded chat, citations, and platform metrics.

Suggested commit:

```text
feat: add streamlit knowledge assistant ui
```

## Phase 12: Kubernetes, Terraform, and Production Hardening

Goal:

Make the project cloud-deployable with Kubernetes manifests, Terraform, secrets strategy, and production runbooks.

Current implementation:

- API image includes Alembic migration assets
- Kubernetes namespace, ConfigMap, Secret example, ServiceAccount, Deployment, Service, migration Job, HPA, and demo Postgres manifests
- Kustomize bundle for rendering the deployment
- provider-neutral Terraform scaffold with deployment inputs and outputs
- AWS Terraform scaffold for VPC, ECR, S3 document storage, RDS PostgreSQL, Secrets Manager, EKS, managed node groups, and IAM policies
- production runbook for release, migration, smoke check, rollback, secrets, and incident response
- deployment validation script and pytest coverage

Architecture:

- Kubernetes deployments and services
- migration job
- worker queues
- Terraform infrastructure
- secret management
- autoscaling policy

Testing:

- manifest validation
- Terraform validation
- container build tests
- smoke tests against deployed environment

Resume bullet:

Prepared the AI knowledge platform for cloud deployment with Kubernetes manifests, Terraform infrastructure, containerized services, secret management, and production runbooks.

Suggested commit:

```text
feat: add kubernetes and terraform deployment
```

## Phase 13: Performance, Security Review, and Portfolio Polish

Goal:

Finalize the project for interviews and portfolio presentation.

Current implementation:

- API load-test script for search, chat, agent, and evaluation workflows
- performance plan with metrics, bottlenecks, and production improvements
- security review covering tenant isolation, prompt injection, upload security,
  authentication, secrets, and infrastructure
- prompt-injection resilience test for citation-preserving agent behavior
- demo script for upload, index, search, chat, agent, evaluation, metrics, and deployment
- portfolio case study
- interview guide with elevator pitch, resume bullets, and expected questions
- portfolio validation script and pytest coverage

Deliverables:

- load tests
- security review
- final README
- screenshots
- architecture diagrams
- demo script
- interview talking points
- portfolio case study

Testing:

- load tests for search and chat
- prompt injection test suite
- dependency and container scans
- end-to-end demo tests

Resume bullet:

Delivered a production-grade enterprise AI platform portfolio project with RAG, hybrid retrieval, agents, evaluation, observability, cloud deployment, security testing, and performance validation.

Suggested commit:

```text
docs: add final portfolio case study and demo guide
```
