# CodeSense — Deployment

**Document Status:** Living Document  
**Version:** 1.0  
**Project:** CodeSense  
**Purpose:** How to build, configure, run, and verify CodeSense in Docker Compose (production-like local deployment).

---

## 1. Overview

CodeSense runs as a single Docker Compose stack (FastAPI + PostgreSQL + Redis + Celery worker + nginx + Prometheus + dashboard). No Kubernetes or microservices. The stack is defined in `docker-compose.yml` at the project root.

| Service | Image / Build | Purpose | Port |
|---|---|---|---|
| postgres | `postgres:16` | Primary database (source of truth) | 5432 |
| redis | `redis:7-alpine` | Cache + Celery broker | 6379 |
| backend | `backend/Dockerfile` | FastAPI API | 8000 |
| worker | `backend/Dockerfile` | Celery background jobs | — |
| simulator | `simulator/Dockerfile` | Standalone external data source | 8001 |
| prometheus | `prom/prometheus:v2.47.0` | Metrics scraping | 9090 |
| dashboard | `frontend/Dockerfile` | React dashboard (served by nginx) | 3000 (via nginx 80) |
| nginx | `nginx:alpine` | Reverse proxy: `/api/v1` → backend, `/` → dashboard | 80 |

All services share the `home-server-backend` network. `postgres_data` and `redis_data` volumes persist across `docker-compose down && up`.

---

## 2. Prerequisites

- Docker + Compose v2 (`docker compose` plugin) or standalone `docker-compose`
- Python 3.12 (for local dev / tests): `.venv`
- PostgreSQL on `localhost:5432` for the test suite (when not using Compose)

Copy the example environment file:

```bash
cp .env.example .env
# Edit .env — set a real SECRET_KEY before any production deploy
```

`SECRET_KEY` must be set via environment variable in production; `backend/app/core/settings.py` refuses to start in `APP_ENV=production` with an insecure default (`changeme`, `supersecretkeyreplaceinproduction`, `dev-only-insecure-change-me`).

---

## 3. Build and run

```bash
# Build and start the full stack (detached)
docker compose up -d --build

# Follow logs
docker compose logs -f

# Stop and remove containers (volumes are preserved)
docker compose down

# Stop and remove containers + named volumes (loses Postgres/Redis data)
docker compose down -v
```

Health checks:
- `postgres`: `pg_isready`
- `redis`: `redis-cli ping`
- `backend`: `curl -f http://localhost:8000/api/v1/health`
- `nginx`: `wget --spider http://localhost:80/health`

Verify the API is reachable through nginx:

```bash
curl http://localhost/health          # nginx self-check -> "ok"
curl http://localhost/api/v1/health   # proxied to backend
curl http://localhost/metrics         # Prometheus scrape target
```

---

## 4. Environment variables

Key variables (full list in `.env.example`):

| Variable | Default | Notes |
|---|---|---|
| `POSTGRES_USER/PASSWORD/DB/PORT` | `postgres`/`postgres`/`codesense`/`5432` | Database credentials |
| `APP_ENV` | `development` | `production` requires a real `SECRET_KEY` |
| `SECRET_KEY` | dev placeholder | JWT signing; **must be set via env in production** |
| `REDIS_HOST/PORT` | `localhost`/`6379` | Cache + broker |
| `ENABLE_REDIS` | `true` | Falls back to in-memory when unavailable |
| `ENABLE_METRICS` | `true` | Prometheus middleware |
| `ENABLE_TRACING` | `false` | OpenTelemetry (no-op if deps missing) |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `` | OTLP trace endpoint |
| `OPENROUTER_API_KEY` | `` | Optional LLM key for AI insights |
| `WORKER_CONCURRENCY` | `2` | Celery worker concurrency |

---

## 5. Database

Migrations live in `database/` and are managed with Alembic (`alembic.ini`).

```bash
# Create a new migration after model changes
alembic revision --autogenerate -m "describe change"

# Apply migrations
alembic upgrade head
```

Data survives `docker compose down && up` because `postgres` mounts `postgres_data:/var/lib/postgresql/data` (see `docker-compose.yml`). To wipe data: `docker compose down -v`.

Backup / restore:

```bash
scripts/db_backup.sh
scripts/db_restore.sh <backup-file>
```

---

## 6. Nginx routing

`docker/nginx/default.conf`:

- `/api/v1` → FastAPI backend (`backend:8000`)
- `/` → dashboard frontend (`dashboard:80`)
- `/health` → nginx self-check (`ok`)

Security-relevant headers are also applied by the FastAPI `SecurityHeadersMiddleware` (see Security Hardening doc).

---

## 7. Verification

- Compose config parses: `docker compose config --quiet` (tested by `tests/integration/test_deploy_compose.py::test_compose_config_valid`, skipped when `docker-compose` is unavailable)
- Postgres volume defined: `tests/integration/test_deploy_compose.py::test_postgres_volume_defined`
- API health: `curl -f http://localhost/api/v1/health` returns `{"status": "ok", ...}`
- Full test suite: `pytest tests/ -q` (one known pre-existing flake: `test_e2e_phases.py::test_end_to_end_integration` — re-run once if it fails)
