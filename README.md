# Enterprise AI Knowledge Platform

Production-style multi-tenant AI knowledge platform for enterprise document intelligence.

This repository contains a complete portfolio project under
[`enterprise-ai-platform/`](enterprise-ai-platform/). It demonstrates secure document upload,
tenant-scoped retrieval, grounded chat, deterministic agent workflows, evaluation, metrics, and
cloud-ready deployment scaffolding.

## What It Shows

- Multi-tenant organization and workspace model
- JWT authentication and RBAC-ready authorization
- Document upload, validation, versioning, and indexing
- Chunking and deterministic local embeddings
- Hybrid retrieval with lexical and vector scoring
- Grounded chat answers with citations
- Agent workflow with traceable plan, retrieval, grounding, and final answer steps
- Evaluation metrics for groundedness, faithfulness, relevance, and context recall
- FastAPI backend and Streamlit console
- Docker, Kubernetes, and Terraform AWS deployment scaffolding
- Production readiness checks including tests, type checks, linting, migrations, and load smoke

## Quick Demo

```bash
cd enterprise-ai-platform/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```bash
cd enterprise-ai-platform
source backend/.venv/bin/activate
pip install -r frontend/requirements.txt
streamlit run frontend/app.py
```

- API docs: `http://127.0.0.1:8000/docs`
- Streamlit console: `http://127.0.0.1:8501`

See the full project README:
[`enterprise-ai-platform/README.md`](enterprise-ai-platform/README.md)
