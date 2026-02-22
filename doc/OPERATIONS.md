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

## Production Rollout Checklist

Use this as a minimal checklist when promoting a new version to production:

- Configuration
  - [ ] Set `ENVIRONMENT=prod`.
  - [ ] Set `JWT_SECRET` to a high‑entropy value from your secret manager.
  - [ ] Configure all `DB_*` variables to point at the managed PostgreSQL instance.
  - [ ] Set `OLLAMA_BASE_URL` to the production Ollama endpoint if it differs from the default `http://ollama.default.svc.cluster.local:11434`.
  - [ ] Set `RATE_LIMIT_PER_MINUTE` to values aligned with your SLOs.

- Database and migrations
  - [ ] Ensure the production database exists and is reachable from the service.
  - [ ] Run Alembic migrations to `head` before switching traffic.
  - [ ] Confirm backups and PITR settings are active and tested.

- Admin and credentials
  - [ ] Run the seeding procedure once (or during bootstrap) to create `admin@example.com`, roles, and bootstrap credentials.
  - [ ] Capture and store `BOOTSTRAP_ADMIN_EMAIL`, `BOOTSTRAP_ADMIN_PASSWORD` and `BOOTSTRAP_ADMIN_API_KEY` in the secret manager.
  - [ ] Rotate the bootstrap API key after initial setup, issuing new keys per service or team.

- Ollama integration
  - [ ] Confirm the Ollama service is reachable from the user‑management API pods/containers.
  - [ ] Confirm at least one chat model and one embeddings model are pulled and available.
  - [ ] Verify a sample chat and embeddings request through the API or frontend.

- Observability and alerts
  - [ ] Verify `/healthz` and `/readyz` responses and that probes are configured correctly.
  - [ ] Confirm metrics are ingested (Prometheus scrape, dashboards rendering).
  - [ ] Validate alert rules for p95 latency, error rate and saturation.

- Security and networking
  - [ ] Validate TLS termination at the edge or ingress.
  - [ ] Confirm that access to Ollama and PostgreSQL is restricted to the service via VPC/firewall rules.
  - [ ] Verify that secrets are loaded from Secret Manager and not baked into images.

- Rollback plan
  - [ ] Define the previous image tag to roll back to.
  - [ ] Confirm that Alembic downgrade strategy and data implications are understood.
  - [ ] Ensure runbooks for rollback are accessible to the on‑call team.
