# Software Architecture

## Executive Summary

EAKP is a multi-tenant enterprise AI knowledge platform. Organizations own workspaces. Workspaces own documents, vector indexes, prompts, agents, conversations, metrics, and access policies. Users interact with the system through APIs and UI clients, while asynchronous workers process documents, build indexes, evaluate responses, and emit observability events.

The architecture uses clean architecture and dependency inversion so high-value business logic is isolated from framework, database, model-provider, and cloud choices.

## System Context

```text
Users and Admins
      |
      v
Streamlit MVP / Future React UI
      |
      v
FastAPI API Gateway
      |
      +--> Auth, RBAC, rate limits, audit logging
      |
      v
Application Services
      |
      +--> Document Ingestion Use Cases
      +--> Search and RAG Use Cases
      +--> Conversation Use Cases
      +--> Agent Use Cases
      +--> Evaluation Use Cases
      |
      v
Domain Model
      |
      +--> Organization, Workspace, Document, Chunk
      +--> Conversation, Message, Agent, PromptVersion
      +--> Evaluation, UsageMetric, AuditEvent
      |
      v
Infrastructure Adapters
      |
      +--> PostgreSQL + pgvector
      +--> Redis
      +--> Object Storage
      +--> Queue Workers
      +--> LLM Gateway
      +--> Observability Stack
```

## Runtime Architecture

```text
                Internet
                   |
                   v
             Cloudflare / WAF
                   |
                   v
             Load Balancer
                   |
                   v
                 NGINX
                   |
                   v
            FastAPI Service
       +-----------+------------+
       |                        |
       v                        v
 PostgreSQL + pgvector        Redis
       |                        |
       v                        v
 Object Storage              Queue Broker
                                |
                                v
                         Worker Services
                                |
            +-------------------+-------------------+
            |                   |                   |
            v                   v                   v
     Text Extraction        Embedding          Evaluation
       Pipeline             Pipeline           Pipeline
            |                   |                   |
            +-------------------+-------------------+
                                |
                                v
                           LLM Gateway
                                |
        +-----------+-----------+-----------+-----------+
        v           v           v           v           v
      OpenAI     Azure AI    Anthropic    Gemini      Local

Observability: Prometheus, Grafana, OpenTelemetry, Jaeger, Loki
```

## Layered Architecture

### Presentation Layer

Responsibilities:

- HTTP routing
- request and response schemas
- authentication middleware integration
- OpenAPI documentation
- stream handling for chat responses
- mapping application exceptions to HTTP responses

Non-responsibilities:

- document processing logic
- retrieval logic
- prompt construction
- authorization policy decisions beyond delegation
- ORM or vector-store calls

### Application Layer

Responsibilities:

- use cases such as `UploadDocument`, `AskQuestion`, `CreateAgent`, `EvaluateAnswer`
- transaction boundaries through a unit of work
- orchestration across repositories, domain services, queues, and gateways
- command/query DTOs
- authorization policy enforcement
- application-level idempotency

Patterns:

- Command handlers for mutations
- Query handlers for reads
- Unit of Work for transactional consistency
- Repository interfaces for persistence
- Ports for LLMs, embeddings, storage, search, queues, and metrics

### Domain Layer

Responsibilities:

- enterprise concepts and invariants
- tenant isolation rules
- document lifecycle state machine
- prompt version selection rules
- citation and groundedness value objects
- domain events such as `DocumentUploaded`, `DocumentIndexed`, `ConversationStarted`

Domain objects should be persistence-ignorant. SQLAlchemy models are infrastructure details, not domain entities.

### Infrastructure Layer

Responsibilities:

- SQLAlchemy repositories
- Alembic migrations
- pgvector adapter
- object storage adapter
- Redis cache adapter
- queue producer and worker adapters
- OpenAI/Azure/Anthropic provider adapters
- OpenTelemetry and Prometheus instrumentation

Infrastructure implements ports defined by the application layer.

## Bounded Contexts

```text
Identity and Access
  Users, roles, permissions, memberships, sessions, audit events

Tenant Knowledge
  Organizations, workspaces, documents, versions, chunks, metadata

Retrieval
  lexical indexes, vector indexes, filters, reranking, citations

Conversation
  conversations, messages, memory policy, exports, feedback

Agent Platform
  agents, tools, instructions, model configuration, execution traces

LLM Platform
  providers, models, prompts, prompt versions, cost tracking

Evaluation
  benchmark datasets, online evaluations, scores, evaluator versions

Operations
  metrics, traces, health, job status, incidents, usage reports
```

## Core Design Patterns

- Repository Pattern: hides persistence details behind interfaces.
- Unit of Work: groups writes and event publication around a transaction boundary.
- Strategy Pattern: selects chunking, retrieval, reranking, embedding, and LLM strategies.
- Adapter Pattern: isolates external providers such as OpenAI, Azure AI, S3, and Redis.
- Factory Pattern: creates provider clients from configuration and tenant policy.
- Specification Pattern: composes metadata and permission filters for retrieval.
- Observer/Event Pattern: emits domain and integration events for async workflows.
- CQRS: separates write use cases from optimized read/query paths.

## Multi-Tenancy Model

The first production-worthy version should use shared infrastructure with strict tenant scoping:

```text
Organization
  |
  +-- Workspace
        |
        +-- Documents
        +-- Chunks
        +-- Conversations
        +-- Agents
        +-- Prompts
        +-- Metrics
```

Isolation controls:

- every tenant-owned row includes `organization_id`
- workspace-owned rows include both `organization_id` and `workspace_id`
- application services require tenant context
- repositories require tenant-scoped query specifications
- vector rows include tenant and workspace metadata
- audit logs include actor, organization, workspace, action, result
- future enterprise tier can move high-value tenants to dedicated databases or namespaces

## AI Gateway

Application code must never call model providers directly. It calls stable ports:

```text
Application Use Case
      |
      v
LLM Gateway Port
      |
      +--> OpenAI Adapter
      +--> Azure OpenAI Adapter
      +--> Anthropic Adapter
      +--> Gemini Adapter
      +--> Local/Ollama Adapter
```

Provider abstraction exists to support:

- cost optimization
- regional data residency
- enterprise customer preference
- model fallback
- A/B testing
- offline testing with fake providers

Tradeoff: abstraction adds interface design work. The benefit is substantial because LLM providers change faster than enterprise APIs should.

## Retrieval Architecture

```text
Question
  |
  v
Query Normalization
  |
  +--> Permission Filter Builder
  +--> Metadata Filter Builder
  |
  v
Hybrid Retrieval
  |
  +--> BM25 / lexical search
  +--> pgvector semantic search
  |
  v
Candidate Merge
  |
  v
Reranking
  |
  v
Context Builder
  |
  v
Prompt Builder
  |
  v
LLM Gateway
  |
  v
Answer + Citations + Metrics + Evaluation Event
```

Initial implementation can use PostgreSQL full-text search plus pgvector. At scale, the lexical path can move to OpenSearch or Elasticsearch without changing application use cases.

## Agent Architecture

Agents are configured business capabilities, not hard-coded chatbots.

```text
Agent Definition
  |
  +-- instructions
  +-- allowed tools
  +-- model policy
  +-- knowledge scope
  +-- memory policy
  +-- permission policy
  |
  v
LangGraph Runtime
  |
  +-- retrieve knowledge
  +-- call tools
  +-- reason
  +-- validate output
  +-- emit trace
```

Initial agents:

- Knowledge Agent: answers grounded questions over workspace documents.
- Policy Agent: summarizes policy documents and highlights compliance constraints.
- Research Agent: synthesizes multiple internal sources with citations.

MCP should be treated as a future external tool boundary. The first version can define an internal tool interface that maps cleanly to MCP later.

## Event-Driven Processing

Document ingestion and evaluation should be asynchronous.

```text
POST /documents
  |
  v
Validate upload and persist metadata
  |
  v
Emit DocumentUploaded
  |
  v
Worker extracts text
  |
  v
Worker chunks content
  |
  v
Worker generates embeddings
  |
  v
Worker indexes vectors
  |
  v
Emit DocumentIndexed
```

Why async:

- large files exceed request latency budgets
- embedding providers are rate limited
- retries and dead-letter queues are operational requirements
- users need job status rather than blocked HTTP requests

## Observability Architecture

Every request and background job should emit:

- trace id
- tenant id
- actor id when available
- operation name
- latency
- external provider latency
- token usage
- estimated cost
- error classification
- queue wait time for jobs

Metrics:

- API latency and error rate
- upload validation failures
- ingestion job duration
- embedding latency and cost
- retrieval latency
- reranking latency
- LLM latency and token usage
- evaluation scores
- cache hit ratio

## Key Engineering Tradeoffs

### PostgreSQL + pgvector vs dedicated vector database

Choose PostgreSQL + pgvector first because it reduces operational complexity, keeps metadata and vector filters close together, and is sufficient for a portfolio-scale and many real enterprise workloads.

Move to a dedicated vector database when vector volume, recall tuning, distributed indexing, or isolation requirements exceed PostgreSQL operations.

### Celery vs Dramatiq

Celery is mature, widely known, and recruiter-friendly. Dramatiq is simpler and often easier to operate. For this portfolio, Celery is acceptable because enterprise reviewers recognize it and it supports scheduled tasks, retries, and result tracking.

### Streamlit vs React MVP

Streamlit is acceptable for the MVP because it demonstrates the AI workflow quickly. React/Next.js should be reserved for the polished product UI milestone.

### LangGraph vs custom orchestration

Use LangGraph for agent workflows where stateful graph execution matters. Do not use it for simple deterministic pipelines such as validation, chunking, or persistence.

