# CodeSense — Troubleshooting

**Document Status:** Living Document  
**Version:** 1.0  
**Project:** CodeSense  
**Purpose:** Common issues, causes, and fixes for CodeSense deployment and operation.

---

## 1. Common issues

| Symptom | Likely cause | Fix |
|---|---|---|
| Backend container unhealthy / restarting | Postgres or Redis not ready yet | Compose `depends_on` with `condition: service_healthy` handles ordering; check `docker compose logs backend` and wait for healthcheck |
| `curl http://localhost/api/v1/health` fails | Backend not up, or wrong port | Confirm `docker compose up -d` completed; backend listens on `8000`, nginx on `80` |
| `429 Rate limit exceeded` | Token bucket (60 req/min per IP) | Wait for `Retry-After` window; raise `RATE_LIMIT_REQUESTS` if needed |
| `SECRET_KEY` production error | `APP_ENV=production` with insecure default | Set a real `SECRET_KEY` via env/`.env` (see Security Hardening) |
| `/metrics` returns `metrics_disabled` | `prometheus_client` not installed | Install `prometheus_client` or expected in this environment |
| Tracing not exported | `OTEL_EXPORTER_OTLP_ENDPOINT` unset or OpenTelemetry missing | Set endpoint; tracing degrades to console/no-op |
| Redis unreachable | Redis down or wrong host | App falls back to in-memory cache/queue; check `redis:6379` |
| Worker not processing jobs | Celery broker (Redis) unavailable | Confirm Redis healthy; check worker logs |
| DB data lost after restart | `docker compose down -v` removed volumes | Use `down` (no `-v`) to preserve `postgres_data`/`redis_data` |
| Migration out of sync | Model changed without `alembic revision --autogenerate` | Generate + apply: `alembic revision --autogenerate -m "..." && alembic upgrade head` |

---

## 2. Logs and inspection

```bash
# All services
docker compose logs

# One service, follow
docker compose logs -f backend

# Health checks
curl -f http://localhost/api/v1/health
curl -f http://localhost/api/v1/health/detailed
curl http://localhost/health        # nginx self-check
curl http://localhost/metrics       # Prometheus target

# Config validation
docker compose config --quiet
```

---

## 3. Backup / restore

```bash
scripts/db_backup.sh          # creates a Postgres dump
scripts/db_restore.sh <file>  # restores a dump into Postgres
```

---

## 4. Tests

Run the suite:

```bash
/home/manoj/Project/CodeSense/.venv/bin/python -m pytest tests/ -q
```

Notes:
- Compose-dependent tests (`test_deploy_compose.py`) skip when `docker-compose` is unavailable.
- One known pre-existing flake: `test_e2e_phases.py::test_end_to_end_integration` (Phase 23 Task 1 fixed it; re-run once if it fails, do not fix).
- Security: `tests/integration/test_security_scan.py`
- Observability: `tests/integration/test_observability.py`, `tests/unit/test_infrastructure.py`
