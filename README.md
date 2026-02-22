# User Management API

## Prerequisites
- pyenv with Python 3.11.10
- Docker and Docker Compose

## Setup
```
make pyenv
make dev-install
```

## Run Locally
```
docker compose -f docker-compose.dev.yml up --build
```

## Environment
- ENVIRONMENT=local|prod
- DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
- JWT_SECRET
- OLLAMA_BASE_URL

## Tests
```
make test
```

## Migrations
```
make upgrade
make migrate
make downgrade
```

## Deployment
- Build image and deploy to Cloud Run with VPC connector.

## Notes
- The service auto-detects Ollama base URL using ENVIRONMENT.
