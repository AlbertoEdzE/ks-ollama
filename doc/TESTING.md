# Testing Strategy and Execution

## Principles
- Real systems only: tests use real PostgreSQL via TestContainers; no mocks.
- Coverage gate: 90% overall; critical auth and credential paths targeted at 100%.
- Repeatable and automated in CI.

## Backend
- Unit: `pytest` under `tests/unit` for services and repositories.
- Integration: `tests/integration` start a Postgres 15 container automatically; API exercised through TestClient.
- Security: `tests/security` checks authentication, authorisation surfaces, security headers, SQL injection prevention, and rate limits.
- Contract: Schemathesis tests validate OpenAPI conformance.
- Performance: `tests/perf` verifies in‑process p95; `perf/locustfile.py` for load and stress.

Run all:
```
pytest
```
Load tests:
```
locust -f perf/locustfile.py
```

## Frontend
- Unit & integration: Vitest + Testing Library.
- Accessibility: jest‑axe rules.
- Cross‑browser E2E: Playwright on Chromium, Firefox, WebKit.

Run:
```
cd frontend
npm i
npm test
npx playwright install --with-deps
npm run test:e2e
```

## Full Integration
- Local stack:
```
docker compose -f docker-compose.dev.yml up --build
```
- Use the frontend at http://localhost:5173 targeting API at http://localhost:8080.

## Resilience and DR
- Chaos tests should be executed in staging: terminate DB or inject latency; observe SLO alerts.
- Backup & restore: verify daily backups, test PITR monthly.

## CI
- See `.github/workflows/ci.yml` for backend and frontend jobs.

## Reporting
- Store coverage artefacts, Locust reports, and Playwright traces for each run.
