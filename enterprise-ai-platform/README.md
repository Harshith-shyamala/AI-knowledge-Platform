# Enterprise AI Knowledge Platform

Enterprise AI Knowledge Platform (EAKP) is a production-style portfolio project that models how an
internal enterprise knowledge assistant should be built: multi-tenant by default, grounded in indexed
documents, measurable, observable, and prepared for cloud deployment.

The platform lets users upload documents into an organization workspace, index them, search across
the indexed knowledge, ask grounded questions, run a deterministic agent workflow, evaluate answer
quality, and inspect service metrics.

## Highlights

- FastAPI backend with clean application, domain, infrastructure, and API boundaries
- Streamlit console for document upload, search, chat, agent runs, evaluation, and metrics
- Organization/workspace tenancy model
- JWT authentication with role-based permission checks
- Tenant-scoped repositories and cross-tenant access tests
- Document upload validation, safe filename handling, versioning, and local storage adapter
- Text extraction, fixed-window chunking, deterministic local embeddings, and indexed chunks
- Hybrid search with lexical and vector scoring
- Grounded chat with citations and question-specific extractive answers
- Deterministic agent workflow with plan, retrieval, evidence inspection, grounding reflection, and final answer
- Evaluation framework for groundedness, faithfulness, answer relevance, and context recall
- Prometheus-style metrics, health checks, readiness checks, structured logging, and request IDs
- Docker, Docker Compose, Kubernetes, and Terraform AWS deployment scaffolding
- Portfolio documentation, demo script, security review, runbook, and performance plan

## Architecture

```text
Presentation
  FastAPI routers, Pydantic schemas, Streamlit UI

Application
  Use cases, commands, authorization checks, chat, retrieval, agents, evaluation

Domain
  Users, organizations, workspaces, documents, versions, chunks, embeddings, conversations, citations

Infrastructure
  SQLAlchemy repositories, unit of work, Alembic migrations, local storage, deployment adapters
```

The project keeps business logic out of framework routes and ORM models. API routes translate HTTP
requests into application commands. Application services enforce permissions and coordinate
repositories through a unit-of-work boundary.

## Core User Flow

1. Register or log in.
2. Select an organization and workspace.
3. Upload a document such as a vendor security policy.
4. Index the document into chunks and embeddings.
5. Search the workspace knowledge.
6. Ask grounded chat questions and inspect citations.
7. Run the agent workflow for traceable reasoning steps.
8. Run evaluation examples and inspect quality scores.
9. Check service metrics and health endpoints.

Example questions for the included vendor policy demo:

- `What evidence is required before vendor onboarding?`
- `How quickly must security incidents be reported?`
- `Can AI tools process confidential customer data?`
- `Summarize the vendor security policy.`

## Technology Stack

- Python, FastAPI, Pydantic, SQLAlchemy, Alembic
- SQLite for local demo and PostgreSQL/pgvector deployment scaffolding
- Deterministic local embedding gateway for repeatable tests
- Streamlit MVP console
- Pytest, pytest-cov, Ruff, MyPy
- Docker and Docker Compose
- Kubernetes manifests with health probes, resource requests, HPA, and migration job
- Terraform generic scaffold and AWS scaffold for VPC, ECR, S3, RDS, Secrets Manager, IAM, and EKS

## Repository Structure

```text
enterprise-ai-platform/
  backend/
    app/
      api/
      application/
      core/
      domain/
      infrastructure/
      schemas/
    alembic/
    tests/
  frontend/
    app.py
  deployment/
    docker/
    kubernetes/
    terraform/
  docs/
    api/
    architecture/
    operations/
    portfolio/
    roadmap/
    security/
  scripts/
```

## Run Locally

Start the API:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Start the Streamlit console from the project root:

```bash
source backend/.venv/bin/activate
pip install -r frontend/requirements.txt
streamlit run frontend/app.py
```

Open:

- API docs: `http://127.0.0.1:8000/docs`
- API health: `http://127.0.0.1:8000/health/live`
- Streamlit console: `http://127.0.0.1:8501`

Default demo credentials in the UI:

- Email: `demo@example.com`
- Password: `correct horse battery staple`

If the demo user does not exist yet, use the Register tab.

## Validation

Core checks:

```bash
cd backend
source .venv/bin/activate
ruff check .
mypy app tests
pytest --cov=app --cov-report=term-missing
```

Deployment and portfolio checks:

```bash
cd ..
source backend/.venv/bin/activate
python scripts/validate_deployment.py
python scripts/validate_portfolio.py
kubectl kustomize deployment/kubernetes
terraform -chdir=deployment/terraform init -backend=false
terraform -chdir=deployment/terraform validate
terraform -chdir=deployment/terraform/aws init -backend=false
terraform -chdir=deployment/terraform/aws validate
```

Load smoke against a running API:

```bash
source backend/.venv/bin/activate
python scripts/load_test_api.py --iterations 10 --email-prefix demo-load
```

Recent local readiness results:

- `ruff check .` passed
- `mypy app tests` passed
- `pytest --cov=app` passed with 41 tests and 93% coverage
- Alembic migrations upgraded to head
- API health, readiness, metrics, Streamlit health passed
- End-to-end user flow passed: register, workspace, upload, index, search, chat, agent, evaluation
- Kubernetes render passed
- Terraform validate passed for generic and AWS scaffolds
- Docker Compose config passed

## Deployment Notes

Docker:

```bash
docker compose -f deployment/docker/docker-compose.yml up --build
```

Kubernetes:

```bash
kubectl apply -k deployment/kubernetes
```

Terraform AWS scaffold:

```bash
cd deployment/terraform/aws
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
```

Before deploying for real users, provide real secrets, configure AWS credentials, replace placeholder
container image names, run Docker image build/container smoke, and complete dependency/security audit
remediation.

## Documentation

- [Architecture](docs/architecture/architecture.md)
- [Data model](docs/architecture/data-model.md)
- [API contract](docs/api/api-contract.md)
- [Sequence diagrams](docs/architecture/sequences.md)
- [Security architecture](docs/security/security-architecture.md)
- [Security review](docs/security/security-review.md)
- [Production runbook](docs/operations/production-runbook.md)
- [Performance plan](docs/operations/performance-plan.md)
- [Demo script](docs/portfolio/demo-script.md)
- [Case study](docs/portfolio/case-study.md)
- [Interview guide](docs/portfolio/interview-guide.md)
- [Milestone roadmap](docs/roadmap/milestones.md)

## Interview Positioning

Short pitch:

> I built a multi-tenant enterprise AI knowledge platform with secure upload, indexing, hybrid
> retrieval, grounded chat, deterministic agent workflows, evaluation metrics, observability, and
> deployment scaffolding across Docker, Kubernetes, and Terraform.

What to emphasize:

- Enterprise architecture, not just prompt engineering
- Tenant isolation and authorization before RAG
- Repeatable local embeddings for deterministic tests
- Grounded answers with citations and evaluation scores
- Operational readiness through health, readiness, metrics, migrations, and deployment manifests
- Honest production readiness assessment with known remaining gaps

## Production Readiness Status

Demo and portfolio ready.

Not yet production-ready for real users until these items are complete:

- Resolve dependency audit findings as upstream fixed versions become available
- Run Docker image build and container smoke with Docker Desktop/daemon running
- Run AWS `terraform plan` with valid credentials and target account permissions
- Replace placeholder Kubernetes secrets and image references
- Add persistent object storage and production database backups
- Add external LLM/embedding provider adapter if replacing deterministic local embeddings
- Add CI workflow at repository root if this nested project layout remains

