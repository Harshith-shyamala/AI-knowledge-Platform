# Demo Script

## Goal

Show a production-shaped enterprise AI knowledge workflow in under ten minutes.

## Setup

Run the API:

```bash
cd backend
. .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Run the UI:

```bash
. backend/.venv/bin/activate
streamlit run frontend/app.py
```

Open:

- API docs: `http://127.0.0.1:8000/docs`
- UI: `http://127.0.0.1:8501`

## Talk Track

### 1. Register

Register a demo user. Explain that registration bootstraps an organization and
assigns the first user an organization-admin role.

### 2. Create Workspace

Create or select the `Knowledge` workspace. Explain that every document,
retrieval query, chat, and evaluation is scoped by organization and workspace.

### 3. Upload

Upload a small Markdown file:

```text
Quarterly access reviews require manager approval and audit evidence.
Vendors require SOC 2 evidence before onboarding.
```

Explain upload validation, content hashing, metadata persistence, and local
storage abstraction.

### 4. Index

Click `Index selected document`. Explain text extraction, chunking, deterministic
embedding gateway, and chunk/embedding persistence.

### 5. Search

Search:

```text
SOC 2 evidence
```

Show chunk, document, version, score, lexical score, and vector score.

### 6. Chat

Ask:

```text
What evidence is required before vendor onboarding?
```

Show grounded answer and citations. Explain that chat persists conversations,
messages, and citations.

### 7. Agent

Ask:

```text
What do quarterly access reviews require?
```

Show plan, search tool, evidence inspection, grounding reflection, final answer,
and citations.

### 8. Evaluation

Run this golden example:

```json
[
  {
    "question": "What do quarterly access reviews require?",
    "expected_answer": "manager approval and audit evidence"
  }
]
```

Show groundedness, faithfulness, answer relevance, context recall, thresholds,
and evaluator versions.

### 9. Metrics

Open the Metrics tab and show Prometheus-style request count and latency metrics.

### 10. Deployment Story

Briefly show:

- Kubernetes manifests
- Alembic migration job
- AWS Terraform scaffold
- production runbook

## Close

The project demonstrates clean architecture, tenant isolation, RAG, agent
orchestration, evaluation, observability, and cloud deployment readiness.
