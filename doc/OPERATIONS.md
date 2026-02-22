# Operations and Runbooks

## Health Checks
- Liveness: GET /healthz
- Readiness: GET /readyz

## Backups
- PostgreSQL daily logical backups using pg_dump.
- Store backups encrypted and test restore monthly.

## Alerts
- SLO: p95 latency, error rate, saturation.
- Configure Alertmanager routes to on-call.

## Rollbacks
- Docker image tags are immutable; redeploy previous tag.
- Alembic downgrade available; ensure data impact is accepted.

## Secrets
- Use GCP Secret Manager for environment variables in production.

## Rate Limits
- Default per-user limit per minute; adjust via environment variable.

