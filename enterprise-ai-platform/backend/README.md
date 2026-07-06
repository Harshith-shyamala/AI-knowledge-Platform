# Backend

FastAPI backend foundation for the Enterprise AI Knowledge Platform.

## Phase 1 Scope

This milestone provides:

- FastAPI app factory
- typed settings
- structured JSON logging
- request ID middleware
- consistent error envelope
- liveness and readiness endpoints
- dependency container for application services
- test harness
- Docker and CI foundation

Business logic should continue to live outside API routes as the platform grows.

## Local Setup

With Poetry:

```bash
poetry install
poetry run uvicorn app.main:app --reload
```

Without Poetry:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

## Tests

```bash
pytest
ruff check .
mypy app tests
```

## Health Endpoints

- `GET /health/live`: process liveness
- `GET /health/ready`: dependency readiness

## Tenancy Endpoints

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `GET /auth/me`
- `POST /organizations`
- `GET /organizations` requires bearer auth and returns only memberships for the current user
- `GET /organizations/{organization_id}`
- `POST /organizations/{organization_id}/workspaces`
- `GET /organizations/{organization_id}/workspaces`

Registration bootstraps an organization and assigns the first user `organization_admin`. Workspace reads and writes require tenant membership permissions.

## Document Endpoints

- `POST /organizations/{organization_id}/workspaces/{workspace_id}/documents`
- `GET /organizations/{organization_id}/workspaces/{workspace_id}/documents`
- `GET /organizations/{organization_id}/workspaces/{workspace_id}/documents/{document_id}`
- `POST /organizations/{organization_id}/workspaces/{workspace_id}/documents/{document_id}/versions`
- `GET /organizations/{organization_id}/workspaces/{workspace_id}/documents/{document_id}/versions`

Uploads validate file size, extension, MIME type, and content hash before storing the file through the storage adapter. Local storage is used in Phase 4; S3-compatible storage can replace it behind the same application port.

## Indexing Endpoints

- `POST /organizations/{organization_id}/workspaces/{workspace_id}/documents/{document_id}/index`
- `GET /organizations/{organization_id}/workspaces/{workspace_id}/documents/{document_id}/chunks`

Phase 5 runs indexing synchronously for demo clarity. The application boundary is shaped so a queue worker can own the same indexing use case later.

## Search Endpoint

- `POST /organizations/{organization_id}/workspaces/{workspace_id}/search`

Search combines lexical overlap and vector similarity over indexed chunks, then returns citation-ready results containing chunk, document, and document-version identifiers.

## Chat Endpoints

- `POST /organizations/{organization_id}/workspaces/{workspace_id}/chat`
- `GET /organizations/{organization_id}/workspaces/{workspace_id}/chat/history`
- `GET /organizations/{organization_id}/workspaces/{workspace_id}/chat/{conversation_id}`

Chat uses the same tenant-scoped retrieval boundary as search, generates a grounded answer, and persists assistant citations back to the exact chunks used as evidence.

## Agent Endpoints

- `POST /organizations/{organization_id}/workspaces/{workspace_id}/agents/runs`

Agent runs execute a deterministic workflow: plan, search workspace knowledge, inspect evidence, reflect on grounding, and produce a final answer with citations and trace metadata. The workflow is shaped so LangGraph or another graph runtime can replace the local orchestrator behind the same API contract later.

## Evaluation Endpoints

- `GET /organizations/{organization_id}/workspaces/{workspace_id}/evaluation`
- `POST /organizations/{organization_id}/workspaces/{workspace_id}/evaluation/runs`

Evaluation runs execute golden question examples through the agent workflow, then score groundedness, faithfulness, answer relevance, and context recall with versioned heuristic evaluators. The API returns per-example scores and aggregate scores for regression testing.

## Metrics Endpoint

- `GET /metrics`

The metrics endpoint returns Prometheus-style text metrics for HTTP request counts, total latency, and max latency by method, route template, and status code. Dynamic paths use route templates so organization and workspace IDs do not explode metric cardinality.

## Migrations

```bash
alembic upgrade head
```

The app can auto-create schema in local mode through `EAKP_AUTO_CREATE_SCHEMA=true`, but versioned Alembic migrations are the production path.

## Docker

From the `enterprise-ai-platform` directory:

```bash
docker compose -f deployment/docker/docker-compose.yml up --build
```
