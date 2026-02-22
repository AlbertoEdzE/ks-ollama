# User Management API and Ollama Integration

This project provides a role‑aware user management API with a React frontend and first‑class integration with an Ollama server for chat and embeddings. It is designed to be easy to run locally for developers and straightforward for DevOps engineers to deploy to container platforms.

The stack consists of:
- FastAPI backend with JWT authentication, RBAC and audit logging
- PostgreSQL database
- React/Vite frontend
- Ollama server (local or remote) for chat and embeddings

---

## 1. Prerequisites

For local development and DevOps use:
- Python 3.11.10 (recommended via `pyenv`)
- Docker and Docker Compose
- Node.js 20+ (only required if running the frontend outside Docker)
- An Ollama deployment (local `ollama serve` or a remote cluster service)

Python toolchain:
```bash
make pyenv        # ensure Python 3.11.10 via pyenv
make dev-install  # create .venv and install runtime + dev requirements
```

---

## 2. Configuration and Environment

The backend configuration is driven by environment variables and wrapped in [`app.config.Settings`](file:///Users/albertohernandez/Documents/projects/ks-ollama/app/config.py#L4-L15).

### 2.1 Core environment variables

- `ENVIRONMENT`  
  - `local` for developer machines and ad‑hoc testing  
  - `prod` for production and production‑like environments

- Database:
  - `DB_USER` (default `app`)
  - `DB_PASSWORD` (default `app`)
  - `DB_HOST` (default `localhost` in local, `db` in container)
  - `DB_PORT` (default `5432`)
  - `DB_NAME` (default `app`)

- Authentication and security:
  - `JWT_SECRET` (required in production; defaulted to `dev-secret` during local runs)
  - `JWT_ALG` (default `HS256`)
  - `RATE_LIMIT_PER_MINUTE` (default `60`)

### 2.2 Ollama connectivity (`OLLAMA_BASE_URL`)

The backend accesses Ollama via `settings.resolved_ollama_base_url()`:
- `OLLAMA_BASE_URL` explicitly set → use this value
- `ENVIRONMENT=prod` and `OLLAMA_BASE_URL` unset → default to `http://ollama.default.svc.cluster.local:11434`
- otherwise (typically local) → default to `http://localhost:11434`

This means:
- **Local**: if you run `ollama serve` locally on port `11434`, you do not need to set anything; the API will talk to `http://localhost:11434` by default.
- **Kubernetes / Cloud Run**: configure `OLLAMA_BASE_URL` to point at your Ollama service if you are not using the default `ollama.default.svc.cluster.local:11434` convention.

### 2.3 Admin bootstrap and API keys

On initial seed (`make seed` or via the run script), the system:
- Ensures `admin` and `user` roles exist.
- Ensures `admin@example.com` exists, is active, and has the `admin` role.
- Manages an admin password and bootstrap API key using:
  - `ADMIN_BOOTSTRAP_PASSWORD`
  - `ADMIN_BOOTSTRAP_PASSWORD_FORCE`

Behaviour:
- When `ADMIN_BOOTSTRAP_PASSWORD_FORCE` is truthy (`1`, `true`, `yes`), the admin password is reset to the value of `ADMIN_BOOTSTRAP_PASSWORD` (or to a randomly generated secret if not provided).
- A one‑time “bootstrap” API key is created for the admin user if it does not already exist.
- These bootstrap values are written to standard output as:
  - `BOOTSTRAP_ADMIN_EMAIL`
  - `BOOTSTRAP_ADMIN_PASSWORD`
  - `BOOTSTRAP_ADMIN_API_KEY`

DevOps usage:
- Capture these values from the logs in your deployment pipeline (for example from `scripts/run.py`, `make seed`, or container logs) and store them securely in your secret manager.
- Use the bootstrap API key for automation and CI until you have a more permanent key management process in place.

---

## 3. Requirements vs Development Requirements

There are two requirements files:

- [`requirements.txt`](file:///Users/albertohernandez/Documents/projects/ks-ollama/requirements.txt)  
  Runtime dependencies required for the service to run:
  - FastAPI, Uvicorn, Gunicorn
  - SQLAlchemy, Alembic, psycopg2‑binary
  - Pydantic, email‑validator
  - Argon2 for credential hashing
  - JWT, HTTPX, structlog, Prometheus instrumentation, SlowAPI rate limiting

- [`requirements-dev.txt`](file:///Users/albertohernandez/Documents/projects/ks-ollama/requirements-dev.txt)  
  Tooling used only during development, testing and security scanning:
  - `pytest`, `pytest-cov` for tests and coverage
  - `testcontainers[postgresql]` for integration tests
  - `schemathesis` for OpenAPI contract testing
  - `bandit`, `safety` for security analysis
  - `ruff`, `black`, `isort`, `mypy` for linting, formatting and type checks
  - `locust` for performance and load testing

Makefile wiring:
- `make install` → create `.venv` and install `requirements.txt`
- `make dev-install` → same as `install`, plus `requirements-dev.txt`

In production images and on DevOps machines that are only running the service, use `requirements.txt`. Reserve `requirements-dev.txt` for CI, local development, and security tooling.

---

## 4. Local Development and scripts/run.py

You have two main ways to run the system locally:

### 4.1 Using Docker Compose directly

Backend, database and frontend all in containers:

```bash
docker compose -f docker-compose.dev.yml up --build
```

This will:
- Start PostgreSQL (`db` service).
- Build and run the backend using the `Dockerfile` (`app` service).
- Start the frontend via Node (`frontend` service).

Default access:
- API: http://localhost:8080 (OpenAPI docs at `/docs`)
- Frontend: http://localhost:5173

The environment variables set in `docker-compose.dev.yml` control the local DB and JWT secret. Ollama is auto‑detected via `ENVIRONMENT` and `OLLAMA_BASE_URL` as described above.

### 4.2 Using `scripts/run.py` (DevOps‑friendly runner)

[`scripts/run.py`](file:///Users/albertohernandez/Documents/projects/ks-ollama/scripts/run.py) orchestrates a full local stack with:
- Local virtual environment
- Dockerised PostgreSQL
- Backend (Gunicorn + Uvicorn worker) running on the host
- Frontend running in the `frontend` Docker service
- Health checks and admin login verification

Basic usage:

```bash
python scripts/run.py              # default: --env dev
python scripts/run.py --env dev    # explicit local mode
python scripts/run.py --env prod   # prod‑style env checks, but still local machine
```

What it does:
1. **Ensure virtual environment**  
   - Creates `.venv` if missing.  
   - Upgrades `pip`.  
   - Installs `requirements.txt` into `.venv`.

2. **Validate environment**  
   - Sets sensible defaults for `ENVIRONMENT`, `DB_*`, and `JWT_SECRET`.  
   - In `prod` mode, enforces that `JWT_SECRET` is set.

3. **Start database (dev)**  
   - Uses `docker-compose.dev.yml` to start only the `db` service.  
   - Detects free host port (`5432` or `5433`), sets `DB_PORT_HOST`.  
   - Waits for both port and actual DB connection readiness.

4. **Migrate and seed**  
   - Runs Alembic migrations to `head`.  
   - Runs `app.db.seed` to create roles, admin user, admin password and bootstrap API key (emitting `BOOTSTRAP_...` values).

5. **Start API**  
   - Chooses an available API port (`8080`, falling back to `8081`–`8083` if busy).  
   - Starts Gunicorn with Uvicorn worker inside `.venv`.  
   - Waits for the port to open.

6. **Health and login checks**  
   - Calls `/healthz` and `/readyz`.  
   - Attempts `/auth/login` as `admin@example.com` with `ADMIN_BOOTSTRAP_PASSWORD` (default `admin` in dev).  
   - Fails fast if any of these checks fail.

7. **Start frontend**  
   - Starts the `frontend` service via `docker-compose.dev.yml` with a dynamically chosen `FRONTEND_PORT` (5173 or 5174).  
   - Sets `VITE_API_BASE` to the decided API port so that the frontend talks to the correct backend.

8. **Optional browser launch**  
   - `--open-browser` will open API docs and the frontend in your default browser.

Flags:
- `--no-backend` – skip database/API, useful if you are already running them.  
- `--no-frontend` – skip starting the frontend container.  
- `--open-browser` – open browser windows after successful startup.

### 4.3 Ollama models for chat and embeddings

The backend uses Ollama for:
- **Chat**: defaults to a general chat model (for example `llama3.2:latest`).  
- **Embeddings**: defaults to an embedding model (for example `nomic-embed-text`).

DevOps should ensure that, on any environment that will serve requests:

1. An Ollama server is running and reachable at the configured `OLLAMA_BASE_URL` (or default).  
2. At least one chat model and one embeddings model are pulled.

On a local machine with Ollama installed:

```bash
ollama serve &
ollama pull llama3.2:latest      # or your preferred chat model
ollama pull nomic-embed-text     # or your preferred embeddings model
```

The frontend will query the backend for the list of available Ollama models and present them as drop‑downs in the UI. If no models are available or the Ollama server is unreachable, the model fields fall back to simple text inputs.

---

## 5. Admin UI and Panels

The React frontend exposes a role‑aware admin interface. After signing in as `admin@example.com` or any user with the `admin` role, the sidebar shows the following panels:

- **User creation** – create new user accounts by email.
- **Admin panel** – manage users, roles, passwords and API credentials.
- **Ollama chat** – send prompts to Ollama chat models.
- **Embeddings** – generate embeddings using Ollama embeddings models.
- **Audit log** – inspect security‑relevant audit events (admin‑only).

Non‑admin users only see:
- **Ollama chat**
- **Embeddings**

### 5.0 Admin quickstart

For a newly bootstrapped environment, an admin can follow this sequence:

1. **Sign in as admin**  
   - Use `admin@example.com` and the password from `BOOTSTRAP_ADMIN_PASSWORD` (or your configured `ADMIN_BOOTSTRAP_PASSWORD`).

2. **Create a user**  
   - Open the **User creation** panel.  
   - Enter the user’s email address.  
   - Click **Create** and confirm the success message.

3. **Assign roles and activate**  
   - Switch to the **Admin panel**.  
   - In “Users & roles”, select the new user.  
   - In “User settings”, tick **Active**.  
   - Tick one or both roles:
     - `user` for standard access (Ollama chat and embeddings).
     - `admin` for full administrative access.
   - Click **Save settings**.

4. **Set an initial password**  
   - Still in **Admin panel**, go to “Set user password”.  
   - Enter a strong password in **New password** and click **Update password**.  
   - Confirm the `Password updated` message.

5. **Issue an API key if required**  
   - In the same Admin panel, open “Credentials”.  
   - Enter a label such as `ci-token` or `service-x`.  
   - Click **Issue** and copy the **one‑time secret** shown.  
   - Store the secret securely (password manager or secret store).

6. **Verify access and audit**  
   - Sign out as admin and sign in as the new user to confirm the correct panels are visible.  
   - Sign back in as admin and use the **Audit log** panel to verify recent `login_success`, `login_failure`, and credential events.

After this initial setup, day‑to‑day administration consists of:
- Creating additional users as needed.  
- Managing roles and active status.  
- Issuing and revoking API keys.  
- Reviewing the Audit log for security and operational insights.

### 5.1 User Creation Panel

Purpose:
- Provision new user accounts that can later sign in via the UI or API.

Inputs and behaviour:
- **Email**: the email address of the new user. This is also the username used for login.
- Click **Create**:
  - On success, the message area shows `Created user@example.com`.
  - On duplicate or invalid email, an error message is shown.
- New users are created as active by default with no roles until assigned in the Admin panel.

Typical usage:
- Admins create individual accounts for engineers, operators or services.
- After creation, switch to the Admin panel to assign roles and set an initial password.

### 5.2 Admin Panel

The Admin panel consists of three functional blocks.

#### Users and roles

- Displays a list of users (email and ID).
- Actions:
  - **Select**: choose a user to manage (for password, roles and credentials).
  - **Refresh**: reload the list from the backend.

Expected inputs:
- None directly; selection is done via the buttons next to each user.

#### User settings

This section manages the selected user’s status and roles:

- **Active** (checkbox):
  - Controls whether the user is allowed to authenticate and use the system.
- **Roles** (checkboxes):
  - `admin`:
    - Grants full access to all panels and admin‑only API endpoints.
    - Enables the User creation, Admin panel and Audit log tabs.
  - `user`:
    - Grants standard access; can use Ollama chat and embeddings panels.

Behaviour:
- Roles are stored as a set of strings and persisted via the backend.
- Admins can combine roles (for example `admin` + `user`) if required.

Typical usage:
- Grant `admin` only to trusted operators.
- Use `user` for application users or services that only need Ollama access.

#### Password management

- **New password**:
  - Sets or updates the selected user’s password.
  - Uses the credential system with label `"password"` and Argon2 hashing.
- Admins should:
  - Set an initial strong password.
  - Rotate passwords on request or according to policy.

### 5.3 API Keys and Credentials

API keys are implemented via the `Credential` model and [`CredentialService`](file:///Users/albertohernandez/Documents/projects/ks-ollama/app/services/credential_service.py#L10-L27):
- Secrets are generated using `secrets.token_urlsafe`.
- Secrets are hashed with Argon2id and only the hash is stored.
- Revocation is supported, and passwords are stored as dedicated credentials with label `"password"`.

### 5.3.1 Bootstrap API key

During seeding, a single bootstrap credential labelled `"bootstrap"` is created for the admin user and emitted as `BOOTSTRAP_ADMIN_API_KEY`. This is intended for:
- Automated scripts.
- Initial CI/CD configuration.

Treat this value as highly sensitive and rotate it via the admin UI or additional tooling if needed.

### 5.3.2 Issuing additional API keys via the UI

In the Admin panel:
1. Select a user in the “Users & roles” list.  
2. In the “Credentials” section:
   - Enter a label (for example `api-key` or `ci-token`).  
   - Click **Issue**.
3. The UI will display a **one‑time secret** labelled “One‑time secret: ...”.  
   - Copy this value and store it securely.  
   - It is not recoverable later, only revokable.
4. The credential list shows:
   - Label and ID.  
   - Revocation status.  
   - A **Revoke** button for active credentials.

Use these API keys wherever non‑interactive or service‑to‑service access is required, for example:
- CI pipelines calling protected endpoints.
- Backend services integrating with the user‑management API.

### 5.4 When to use passwords vs API keys

- **Password + JWT**:
  - Best for interactive human users signing in through the frontend or CLI.
  - Sessions are short‑lived and can be revoked by disabling the user or changing the password.

- **API keys**:
  - Best for machine‑to‑machine or long‑running integrations.
  - Use different keys per system to allow fine‑grained revocation.

Admins should prefer:
- Passwords for people.
- API keys for services, CI and automation.

### 5.5 Audit Log Panel

The Audit log panel surfaces security‑relevant events recorded in the `audit_logs` table and exposed via the `/audit` endpoint.

Data captured (`AuditLog` model):
- `event_type`: short code describing the event (for example `login_success`, `login_failure`, `logout`, `api_key_issued`, `api_key_revoked`).
- `occurred_at`: timestamp of the event.
- `user_id`: optional user identifier associated with the event.
- `credential_id`: optional credential identifier (for API key‑related events).
- `ip`: source IP address, when available.
- `user_agent`: HTTP user agent, when available.
- `detail`: optional free‑form detail string.

UI behaviour:
- **Limit**: number of records to fetch (bounded between 1 and 500).
- **Filter by event type**: simple substring filter applied on `event_type` in the UI.
- **Load**:
  - Fetches the latest events from `/audit?limit=...`.
  - Requires an authenticated admin; non‑admins are denied.
- Table columns:
  - Time
  - Event
  - User
  - IP
  - Agent

Typical usage by admins and DevOps:
- Investigate authentication activity:
  - Check for repeated `login_failure` events from a single IP.
  - Verify successful `login_success` events for troubleshooting.
- Trace credential operations:
  - Confirm when an API key was issued (`api_key_issued`) and for which user.
  - Confirm when a key was revoked (`api_key_revoked`).
- Support incident response:
  - Filter by event type and time window to understand the sequence of actions.

Audit log access is restricted to admin users and should be treated as sensitive operational data.

---

## 6. Docker and Deployment

### 6.1 Backend image

The backend Docker image is defined in [`Dockerfile`](file:///Users/albertohernandez/Documents/projects/ks-ollama/Dockerfile):
- Multi‑stage build:
  - Build stage: `python:3.11-slim`, installs `requirements.txt` and builds wheels into `/wheels`.
  - Runtime stage: `gcr.io/distroless/python3-debian12:nonroot` for a minimal, non‑root container.
- Runtime configuration:
  - `WORKDIR /app`
  - `ENV PYTHONUNBUFFERED=1`
  - `ENV PYTHONPATH=/app`
  - `EXPOSE 8080`
  - Entrypoint: `python -m gunicorn -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080 app.main:app`

This image is suitable for Kubernetes, Cloud Run or any container‑native platform.

### 6.2 Development Compose (`docker-compose.dev.yml`)

[`docker-compose.dev.yml`](file:///Users/albertohernandez/Documents/projects/ks-ollama/docker-compose.dev.yml) defines:
- `db` – PostgreSQL 15 with local volume `db_data`.  
- `app` – Backend built from the local `Dockerfile`, configured with:
  - `ENVIRONMENT=local`
  - Database environment pointing at `db`
  - `JWT_SECRET=dev-secret`
- `frontend` – Node 20 container, maps the repository as a volume:
  - Installs dependencies (`npm i`) and runs `npm run dev` on a configurable port.
  - Takes `VITE_API_BASE` to know where the backend is.

Use this file for local development where you want everything inside Docker.

### 6.3 Production Compose (`docker-compose.prod.yml`)

[`docker-compose.prod.yml`](file:///Users/albertohernandez/Documents/projects/ks-ollama/docker-compose.prod.yml) defines:
- `db` – PostgreSQL 15 with persistent volume.  
- `app` – Uses a pre‑built image `user-management-api:latest` and configures:
  - `ENVIRONMENT=prod`
  - `DB_*` pointing at the `db` service
  - `JWT_SECRET=change-me` (must be overridden in real deployments)
  - `OLLAMA_BASE_URL=http://ollama.default.svc.cluster.local:11434` (override as appropriate)

To run:

```bash
docker build -t user-management-api:latest .
docker compose -f docker-compose.prod.yml up -d
```

In production, you will typically:
- Replace `user-management-api:latest` with a CI‑built, signed image tag.  
- Override `JWT_SECRET`, `OLLAMA_BASE_URL`, and database credentials via environment or a secrets manager.  
- Configure a VPC connector or networking to reach your Ollama deployment if it is running in a separate cluster.

---

## 7. Tests and Quality Gates

Backend tests:

```bash
make test          # pytest with coverage (see pytest.ini for thresholds)
make lint          # ruff, mypy, bandit
```

Frontend tests:

```bash
cd frontend
npm install
npm test           # Vitest unit and integration
npm run test:e2e   # Playwright E2E (requires a running stack)
```

Testing strategy, tooling and CI are further documented in:
- [`doc/TESTING.md`](file:///Users/albertohernandez/Documents/projects/ks-ollama/doc/TESTING.md)
- GitHub Actions workflows in `.github/workflows/`

---

## 8. Operations and Further Reading

For SRE/DevOps teams, additional operational details live under `doc/`:
- [`doc/SETUP.md`](file:///Users/albertohernandez/Documents/projects/ks-ollama/doc/SETUP.md) – step‑by‑step setup guide for local and production.  
- [`doc/OPERATIONS.md`](file:///Users/albertohernandez/Documents/projects/ks-ollama/doc/OPERATIONS.md) – health checks, backups, alerts, rollbacks and secrets guidance.  
- [`doc/user_management_design.md`](file:///Users/albertohernandez/Documents/projects/ks-ollama/doc/user_management_design.md) – full architecture and design document.

These documents, together with this README, should give DevOps engineers all the information required to:
- Provision the database and Ollama services.  
- Build and deploy the API and frontend.  
- Manage admin credentials and API keys.  
- Monitor, test and operate the system safely in production.
