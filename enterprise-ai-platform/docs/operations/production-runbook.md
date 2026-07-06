# Production Runbook

## Release Flow

1. Build and tag the API image.
2. Push the image to the container registry.
3. Update `deployment/kubernetes/kustomization.yaml` with the image tag.
4. Apply secrets from the cloud secret manager.
5. Run the Alembic migration job.
6. Deploy the API rollout.
7. Verify health, readiness, metrics, search, chat, agent, and evaluation smoke checks.

## AWS Terraform Flow

1. Copy `deployment/terraform/aws/terraform.tfvars.example` to `terraform.tfvars`.
2. Replace `database_password` and `jwt_secret_key`.
3. Run `terraform init`, `terraform plan`, and `terraform apply`.
4. Build and push the API image to the `ecr_repository_url` output.
5. Configure kubectl with the `kubectl_update_command` output.
6. Update `deployment/kubernetes/kustomization.yaml` with the `api_image` output.
7. Apply the Kubernetes bundle.

## Migration

Run migrations before rolling the API:

```bash
kubectl -n eakp create job --from=job/eakp-api-migrate eakp-api-migrate-manual
kubectl -n eakp logs job/eakp-api-migrate-manual
```

If migration fails, stop the rollout and inspect the job logs before retrying.

## Smoke Checks

```bash
kubectl -n eakp port-forward service/eakp-api 8000:80
curl http://127.0.0.1:8000/health/live
curl http://127.0.0.1:8000/health/ready
curl http://127.0.0.1:8000/metrics
```

## Rollback

1. Stop new rollout traffic if your ingress supports it.
2. Revert the image tag in `kustomization.yaml`.
3. Apply the previous manifest.
4. Confirm `/health/ready` returns `ready`.

Database rollbacks require a migration-specific plan. Do not downgrade blindly.

## Secrets

Required secrets:

- `EAKP_DATABASE_URL`
- `EAKP_JWT_SECRET_KEY`

Never commit production secret values. Use cloud secret manager injection or
sealed/encrypted Kubernetes secrets.

## Incident Checklist

- Check pod status and recent restarts.
- Check `/health/ready`.
- Inspect API logs by request ID.
- Inspect database connectivity and migration status.
- Inspect `/metrics` for elevated 5xx counts or latency.
- Roll back only after identifying whether the issue is app, config, database, or infrastructure.
