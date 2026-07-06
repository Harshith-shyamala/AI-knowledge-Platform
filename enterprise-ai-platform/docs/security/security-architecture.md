# Security Architecture

## Security Goals

- Prevent cross-tenant data exposure.
- Enforce role-based access to documents, agents, prompts, and metrics.
- Protect file upload and ingestion pipelines.
- Reduce prompt injection and data exfiltration risk.
- Provide auditability for enterprise operations.
- Keep secrets out of code, logs, and client responses.

## Identity and Access

Initial version:

- JWT authentication
- password hashing with a modern algorithm
- refresh token rotation
- organization and workspace memberships
- role-based permissions

Future-ready:

- OAuth2
- Google login
- Microsoft login
- GitHub login
- SAML/SSO
- MFA

## RBAC Model

Roles:

- `super_admin`: platform-wide operational access
- `organization_admin`: manages organization users, workspaces, billing, settings
- `manager`: views dashboards and team activity
- `knowledge_editor`: uploads, versions, and deletes documents
- `standard_user`: searches and chats with permitted knowledge
- `guest`: limited read-only access

Permissions should be represented as capabilities such as:

- `documents.upload`
- `documents.delete`
- `documents.search`
- `agents.create`
- `metrics.view`
- `billing.manage`
- `users.invite`

## Tenant Isolation

Controls:

- tenant context required in application services
- repository methods scoped by organization and workspace
- vector search filters include tenant identifiers
- audit log on permission failures
- row-level security as defense in depth in later milestone

## Secure Uploads

Validation steps:

- file size limit
- MIME type validation
- extension allowlist
- content hash computation
- duplicate detection
- virus scan placeholder in MVP, real scanner later
- OCR sandboxing for scanned PDFs later
- storage key generated server-side

## Prompt Injection Defense

Prompt injection cannot be solved with a single filter. Use layered controls:

- classify retrieved content for suspicious instructions
- isolate system instructions from document content
- quote retrieved context with clear boundaries
- deny tool calls not allowed by agent policy
- apply output validation for sensitive workflows
- log suspicious prompts and document chunks
- never allow retrieved text to modify authorization policy

## PII and Secret Handling

Controls:

- PII detection during ingestion
- optional PII masking before prompts
- secret pattern detection for API keys and credentials
- redaction in logs
- configurable tenant policy for storing raw extracted text

## Rate Limiting

Rate limit dimensions:

- IP address
- user id
- organization id
- endpoint
- provider budget

LLM-heavy endpoints should have stricter tenant-level quotas than simple metadata reads.

## Audit Logging

Audit events:

- login success and failure
- document upload, delete, restore
- search and chat execution
- agent creation and execution
- prompt version activation
- role changes
- billing or budget changes
- permission denial

Audit logs are append-only and should not be hard-deleted.

## Secrets

Local development:

- `.env` ignored by git
- example env files only contain safe placeholders

Production:

- cloud secrets manager
- Kubernetes secrets synced from secret manager
- rotation policy for provider API keys
- no secrets in Terraform state

## Security Testing

Required test categories:

- tenant isolation integration tests
- permission matrix tests
- upload validation tests
- prompt injection fixtures
- PII masking fixtures
- dependency vulnerability scans
- container image scans

