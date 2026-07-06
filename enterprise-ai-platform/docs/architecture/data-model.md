# Data Model and Tenancy Design

## Modeling Principles

- Tenant-owned data must be scoped by `organization_id`.
- Workspace-owned data must be scoped by `organization_id` and `workspace_id`.
- Access checks must happen before retrieval, not after generation.
- Document versions are immutable once indexed.
- Soft delete is required for enterprise auditability.
- Audit logs are append-only.
- Evaluation records must preserve model, prompt, retriever, and evaluator versions.

## Core Entity Relationship Diagram

```text
organizations
  |
  +-- organization_memberships -- users
  |
  +-- workspaces
        |
        +-- workspace_memberships
        |
        +-- documents
        |     |
        |     +-- document_versions
        |            |
        |            +-- chunks
        |                  |
        |                  +-- embeddings
        |
        +-- conversations
        |     |
        |     +-- messages
        |           |
        |           +-- citations
        |           +-- feedback
        |
        +-- agents
        |     |
        |     +-- agent_tools
        |     +-- agent_runs
        |
        +-- prompts
        |     |
        |     +-- prompt_versions
        |
        +-- evaluations
        +-- usage_metrics
        +-- audit_logs
```

## Tables

### users

Stores global identities. A user may belong to many organizations.

Key fields:

- `id`
- `email`
- `display_name`
- `hashed_password`
- `is_active`
- `email_verified_at`
- `mfa_enabled`
- `created_at`
- `updated_at`

### organizations

Represents a tenant.

Key fields:

- `id`
- `name`
- `slug`
- `plan`
- `status`
- `settings_json`
- `created_at`
- `updated_at`

### organization_memberships

Maps users to organizations and high-level roles.

Key fields:

- `id`
- `organization_id`
- `user_id`
- `role`
- `created_at`

Roles:

- `super_admin`
- `organization_admin`
- `manager`
- `knowledge_editor`
- `standard_user`
- `guest`

### workspaces

Represents an isolated knowledge area within an organization.

Key fields:

- `id`
- `organization_id`
- `name`
- `slug`
- `description`
- `settings_json`
- `created_at`
- `updated_at`

### workspace_memberships

Allows workspace-level access control.

Key fields:

- `id`
- `organization_id`
- `workspace_id`
- `user_id`
- `role`
- `created_at`

### documents

Represents a logical document across versions.

Key fields:

- `id`
- `organization_id`
- `workspace_id`
- `owner_user_id`
- `title`
- `source_type`
- `source_uri`
- `mime_type`
- `status`
- `tags_json`
- `metadata_json`
- `current_version_id`
- `deleted_at`
- `created_at`
- `updated_at`

Statuses:

- `uploaded`
- `validating`
- `extracting`
- `chunking`
- `embedding`
- `indexed`
- `failed`
- `deleted`

### document_versions

Immutable file and extraction record.

Key fields:

- `id`
- `organization_id`
- `workspace_id`
- `document_id`
- `version_number`
- `storage_key`
- `file_sha256`
- `size_bytes`
- `extracted_text_sha256`
- `extraction_metadata_json`
- `created_by_user_id`
- `created_at`

Unique constraints:

- `(document_id, version_number)`
- `(organization_id, workspace_id, file_sha256)` for deduplication hints

### chunks

Stores chunk text and retrieval metadata.

Key fields:

- `id`
- `organization_id`
- `workspace_id`
- `document_id`
- `document_version_id`
- `chunk_index`
- `content`
- `content_sha256`
- `token_count`
- `page_start`
- `page_end`
- `section_title`
- `metadata_json`
- `created_at`

Indexes:

- `(organization_id, workspace_id, document_id)`
- PostgreSQL full-text index on `content`
- metadata GIN index where needed

### embeddings

Stores vector representation for chunks.

Key fields:

- `id`
- `organization_id`
- `workspace_id`
- `chunk_id`
- `provider`
- `model`
- `dimensions`
- `embedding`
- `created_at`

Indexes:

- pgvector approximate nearest neighbor index on `embedding`
- compound indexes for tenant and workspace filters

### conversations

Key fields:

- `id`
- `organization_id`
- `workspace_id`
- `user_id`
- `title`
- `status`
- `memory_policy`
- `created_at`
- `updated_at`
- `deleted_at`

### messages

Key fields:

- `id`
- `organization_id`
- `workspace_id`
- `conversation_id`
- `role`
- `content`
- `model_provider`
- `model_name`
- `prompt_version_id`
- `token_usage_json`
- `latency_ms`
- `created_at`

Roles:

- `user`
- `assistant`
- `tool`
- `system`

### citations

Key fields:

- `id`
- `organization_id`
- `workspace_id`
- `message_id`
- `document_id`
- `document_version_id`
- `chunk_id`
- `quote`
- `score`
- `created_at`

### agents

Key fields:

- `id`
- `organization_id`
- `workspace_id`
- `name`
- `description`
- `instructions`
- `model_policy_json`
- `knowledge_scope_json`
- `memory_policy_json`
- `is_active`
- `created_at`
- `updated_at`

### prompts and prompt_versions

Prompts are logical prompt families. Prompt versions are immutable executable templates.

Key fields:

- `prompts.id`
- `prompts.organization_id`
- `prompts.workspace_id`
- `prompts.name`
- `prompts.purpose`
- `prompt_versions.id`
- `prompt_versions.prompt_id`
- `prompt_versions.version`
- `prompt_versions.template`
- `prompt_versions.status`
- `prompt_versions.created_at`

Statuses:

- `draft`
- `approved`
- `active`
- `retired`

### evaluations

Key fields:

- `id`
- `organization_id`
- `workspace_id`
- `conversation_id`
- `message_id`
- `evaluator_name`
- `evaluator_version`
- `faithfulness_score`
- `groundedness_score`
- `answer_relevance_score`
- `context_precision_score`
- `context_recall_score`
- `hallucination_score`
- `metadata_json`
- `created_at`

### audit_logs

Append-only security and compliance trail.

Key fields:

- `id`
- `organization_id`
- `workspace_id`
- `actor_user_id`
- `action`
- `resource_type`
- `resource_id`
- `result`
- `ip_address`
- `user_agent`
- `metadata_json`
- `created_at`

### usage_metrics

Aggregated and raw usage events.

Key fields:

- `id`
- `organization_id`
- `workspace_id`
- `user_id`
- `metric_type`
- `quantity`
- `unit`
- `cost_usd`
- `provider`
- `model`
- `metadata_json`
- `occurred_at`

## Tenant Isolation Rules

Application services receive a `TenantContext`:

```text
TenantContext
  organization_id
  workspace_id
  actor_user_id
  roles
  permissions
  trace_id
```

Repositories must accept tenant context or scoped specifications. Unscoped repository methods should not exist for tenant-owned data.

## Row Level Security

PostgreSQL row-level security can be added after the first working version. The application should still enforce tenant context because RLS is a defense-in-depth control, not a replacement for application authorization.

## Vector Search Filtering

Vector queries must include:

- `organization_id`
- `workspace_id`
- document permission filters
- document status equals `indexed`
- optional metadata filters such as author, department, tag, source, date

## Versioning Policy

- Uploading changed content creates a new document version.
- Existing chunks and embeddings remain immutable.
- Current search uses `documents.current_version_id`.
- Evaluation and citation records keep the exact version and chunk used at answer time.

