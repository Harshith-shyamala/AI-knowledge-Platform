# Security Review

## Scope

This review covers the local MVP and production scaffolding for EAKP.

## Tenant Isolation

Controls:

- organization and workspace IDs are carried through document, chunk, embedding,
  search, chat, agent, and evaluation flows
- repository methods require tenant scope for tenant-owned data
- cross-tenant API tests cover auth, documents, search, chat, and agents
- RBAC permissions gate organization, workspace, document, search, and metrics
  operations

Residual Risks:

- workspace-level memberships are not yet separate from organization membership
- production should add database-level row-level security or policy checks for
  defense in depth

## Prompt Injection

Controls:

- current deterministic answer generator limits generated behavior
- agent workflow cites retrieved chunks and includes grounding reflection
- evaluation can flag ungrounded answers

Residual Risks:

- real LLM provider integration needs prompt-injection test fixtures
- retrieved content should be treated as untrusted context in future prompts
- tool permissions should be explicit per agent/tool

## Upload Security

Controls:

- empty files rejected
- file size limit enforced
- extensions validated
- safe text extensions tolerate generic browser MIME values
- storage keys include tenant and document IDs
- filenames are sanitized before storage

Residual Risks:

- production should add malware scanning
- production should parse Office/PDF formats in sandboxed workers
- production should store files in S3 with encryption and lifecycle policies

## Authentication And Authorization

Controls:

- JWT access/refresh token flow
- PBKDF2 password hashing
- role-based permission policy
- bearer-token dependency for protected routes

Residual Risks:

- production should add refresh token rotation and revocation
- production should add rate limiting and account lockout protections
- production should integrate SSO/SAML/OIDC

## Secrets

Controls:

- `.env` ignored
- Kubernetes secrets are separated from config
- AWS Terraform creates Secrets Manager entries
- production runbook warns against committing real secret values

Residual Risks:

- Kubernetes secret delivery should use a cloud-native secret operator or sealed
  secrets
- Terraform state can contain sensitive values and needs encrypted remote state

## Infrastructure

Controls:

- Kubernetes probes and resource limits
- non-root container user
- migration job separated from API rollout
- AWS Terraform uses private RDS and private node subnets
- S3 public access blocked and encryption enabled

Residual Risks:

- add private-only EKS control plane access for production
- add ingress/WAF/TLS configuration
- add centralized logs, traces, and alerting
- add cost budgets and resource quotas

## Recommended Next Security Tests

- prompt injection fixture suite
- tenant isolation fuzz tests
- upload MIME/extension bypass tests
- dependency vulnerability scan
- container image scan
- Terraform policy scan
- Kubernetes manifest policy scan
