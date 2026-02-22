# Setup Guide

## Local Development
1. Ensure Python 3.11.10 via pyenv:
```
make pyenv
```
2. Create virtual environment and install:
```
make dev-install
```
3. Start stack:
```
docker compose -f docker-compose.dev.yml up --build
```
4. Apply migrations and seed:
```
make upgrade
make seed
```
5. Open API docs at http://localhost:8080/docs

## Environment Variables
- ENVIRONMENT=local|prod
- DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
- JWT_SECRET
- OLLAMA_BASE_URL

## Production Container
```
docker build -t user-management-api:latest .
docker compose -f docker-compose.prod.yml up -d
```

## Cloud Run
- Configure a VPC connector to access the private Kubernetes Ollama service.
- Set environment variables, mount secrets from Secret Manager.

