# Kubernetes Deployment

This folder contains a production-shaped Kubernetes scaffold for the EAKP API.

## Files

- `namespace.yaml`: namespace and ownership labels
- `configmap.yaml`: non-secret runtime settings
- `secret.example.yaml`: example database and JWT secrets
- `serviceaccount.yaml`: API service account
- `api-deployment.yaml`: FastAPI deployment with health probes and resource limits
- `api-service.yaml`: internal ClusterIP service
- `migration-job.yaml`: one-shot Alembic migration job
- `hpa.yaml`: CPU-based autoscaling policy
- `postgres-demo.yaml`: demo Postgres + pgvector StatefulSet for non-production clusters
- `kustomization.yaml`: deployable bundle

## Deploy

Replace image names and secrets before applying:

```bash
kubectl apply -k deployment/kubernetes
kubectl -n eakp create job --from=job/eakp-api-migrate eakp-api-migrate-manual
```

For production, prefer a managed PostgreSQL service and replace `postgres-demo.yaml`
with a secret containing the managed database URL.
