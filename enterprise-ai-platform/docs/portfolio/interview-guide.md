# Interview Guide

## Elevator Pitch

I built a production-shaped enterprise AI knowledge platform with secure
multi-tenancy, document ingestion, hybrid retrieval, grounded chat, agent
orchestration, evaluation, observability, Streamlit UI, Kubernetes manifests, and
AWS Terraform scaffolding.

## Resume Bullets

- Built a multi-tenant enterprise AI knowledge platform using FastAPI,
  SQLAlchemy, Alembic, JWT auth, RBAC, and clean architecture.
- Implemented secure document upload, versioning, text extraction, chunking,
  embedding persistence, hybrid retrieval, and citation-ready search.
- Built grounded RAG chat and deterministic agent orchestration with traceable
  planning, tool use, evidence inspection, grounding reflection, and citations.
- Added an evaluation framework for groundedness, faithfulness, answer relevance,
  and context recall with versioned evaluators and aggregate scores.
- Added Prometheus-style metrics, Streamlit demo UI, Kubernetes deployment
  manifests, migration jobs, AWS Terraform infrastructure scaffold, and production
  runbooks.

## Questions To Expect

### Why clean architecture?

It keeps business workflows independent of FastAPI, SQLAlchemy, storage, and
model providers. That made it easy to add chat, agents, evaluation, and UI without
rewriting the core.

### How is tenant isolation enforced?

Repository protocols and implementations require organization/workspace IDs on
tenant-scoped reads. API routes also require RBAC permissions before calling use
cases.

### Why deterministic embeddings and answer generation?

They make local demos and tests repeatable. The provider interfaces are shaped so
OpenAI, Azure AI, or internal models can replace them later.

### How do you prevent hallucinations?

The system retrieves tenant-scoped chunks first, stores citations, returns
source chunk/document/version IDs, and evaluates groundedness and context recall.

### How would you scale this?

Move indexing and evaluation to queue workers, use PostgreSQL with pgvector,
store documents in S3, use managed Kubernetes or ECS, add provider-based LLM
gateways, and use OpenTelemetry/Grafana for operations.

### What are the main production gaps?

Remote Terraform state, real secret injection into Kubernetes, managed
observability, async workers, rate limiting, WAF/ingress, full LLM provider
adapter, prompt-injection hardening, and load testing against real infrastructure.

## Demo Timing

- 1 minute: architecture and product vision
- 2 minutes: upload/index/search
- 2 minutes: chat/citations
- 2 minutes: agent trace/evaluation
- 1 minute: metrics/deployment/Terraform
- 2 minutes: security and production tradeoffs
