# API Contract

## Design Principles

- APIs are tenant-aware.
- Routes stay thin and delegate to application services.
- Every mutating endpoint emits audit logs.
- Long-running tasks return job status instead of blocking.
- Error responses use a consistent envelope.
- Streaming chat uses server-sent events in the first production version.

## Common Headers

```text
Authorization: Bearer <jwt>
X-Organization-Id: <uuid>
X-Workspace-Id: <uuid>
X-Request-Id: <uuid>
```

## Error Envelope

```json
{
  "error": {
    "code": "document.unsupported_file_type",
    "message": "The uploaded file type is not supported.",
    "details": {
      "mime_type": "application/octet-stream"
    },
    "request_id": "req_123"
  }
}
```

## Authentication

### POST /auth/register

Creates a user and optional organization bootstrap record.

### POST /auth/login

Returns access and refresh tokens.

### POST /auth/refresh

Rotates access tokens using a refresh token.

## Organizations and Workspaces

### GET /organizations

Lists organizations visible to the current user.

### POST /organizations

Creates an organization.

### GET /workspaces

Lists workspaces for the selected organization.

### POST /workspaces

Creates a workspace.

## Documents

### POST /documents

Uploads a document and starts asynchronous ingestion.

Supported inputs:

- PDF
- Word
- PowerPoint
- Excel
- Markdown
- TXT
- HTML
- CSV

Response:

```json
{
  "document_id": "doc_123",
  "version_id": "ver_123",
  "status": "uploaded",
  "job_id": "job_123"
}
```

### GET /documents

Lists documents with filters.

Query parameters:

- `status`
- `tag`
- `source_type`
- `created_after`
- `created_before`
- `limit`
- `cursor`

### GET /documents/{document_id}

Returns document metadata and current indexing status.

### DELETE /documents/{document_id}

Soft deletes a document.

### GET /documents/{document_id}/versions

Lists document versions.

## Jobs

### GET /jobs/{job_id}

Returns async job status.

Response:

```json
{
  "job_id": "job_123",
  "status": "running",
  "stage": "embedding",
  "progress": 0.72,
  "started_at": "2026-06-29T16:00:00Z",
  "completed_at": null,
  "error": null
}
```

## Search

### POST /search

Performs tenant-scoped hybrid retrieval.

Request:

```json
{
  "query": "What is our vendor security review process?",
  "top_k": 10,
  "filters": {
    "tags": ["security", "procurement"],
    "department": "legal"
  },
  "rerank": true
}
```

Response:

```json
{
  "results": [
    {
      "chunk_id": "chunk_123",
      "document_id": "doc_123",
      "title": "Vendor Security Policy",
      "score": 0.91,
      "page_start": 4,
      "page_end": 5,
      "snippet": "Security review is required before onboarding..."
    }
  ],
  "latency_ms": 118
}
```

## Chat

### POST /chat

Creates or continues a conversation and returns a grounded answer.

Request:

```json
{
  "conversation_id": null,
  "agent_id": "agent_knowledge",
  "message": "Summarize the SOC 2 requirements in our vendor process.",
  "stream": false
}
```

Response:

```json
{
  "conversation_id": "conv_123",
  "message_id": "msg_456",
  "answer": "Vendors must complete security intake, provide SOC 2 evidence, and receive risk approval before production access.",
  "citations": [
    {
      "document_id": "doc_123",
      "chunk_id": "chunk_456",
      "title": "Vendor Security Policy",
      "page": 4,
      "score": 0.89
    }
  ],
  "usage": {
    "input_tokens": 1880,
    "output_tokens": 142,
    "estimated_cost_usd": 0.012
  }
}
```

### POST /chat/stream

Streams answer tokens and final citations over server-sent events.

Event types:

- `retrieval_started`
- `retrieval_completed`
- `token`
- `citation`
- `usage`
- `done`
- `error`

### GET /chat/history

Lists conversations.

### GET /chat/{conversation_id}

Returns messages and citations for a conversation.

### DELETE /chat/{conversation_id}

Soft deletes a conversation.

## Agents

### GET /agents

Lists available agents.

### POST /agents

Creates an agent definition.

### POST /agents/{agent_id}/runs

Executes an agent workflow.

## Evaluation

### GET /evaluation

Returns evaluation metrics.

Query parameters:

- `from`
- `to`
- `agent_id`
- `prompt_version_id`
- `model`

### POST /evaluation/runs

Starts evaluation over a dataset or conversation sample.

## Administration

### GET /admin/dashboard

Returns high-level metrics:

- document counts by status
- token usage
- model latency
- search latency
- embedding cost
- active users
- evaluation scores

## Health and Metrics

### GET /health/live

Returns process liveness.

### GET /health/ready

Checks database, Redis, queue, and model-provider readiness.

### GET /metrics

Prometheus metrics endpoint.

