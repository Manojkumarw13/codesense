# CodeSense — Observability

**Document Status:** Living Document  
**Version:** 1.0  
**Project:** CodeSense  
**Purpose:** Logs, metrics, tracing, and health checks for CodeSense.

---

## 1. Overview

Observability is built into the FastAPI app (`backend/app/main.py`) plus Compose-level health checks and a Prometheus scrape target. It degrades gracefully: if `prometheus_client` or OpenTelemetry are unavailable, the app keeps running with metrics/tracing disabled.

| Layer | Implementation | File |
|---|---|---|
| Metrics | Prometheus (`prometheus_client`) + `PrometheusMiddleware` | `backend/app/core/observability.py` |
| Metrics endpoint | `/metrics` (root) | `backend/app/main.py` |
| Tracing | OpenTelemetry (`setup_tracing`, optional OTLP exporter) | `backend/app/core/observability.py` |
| Logging | Structured request/response logging + `X-Request-ID` | `backend/app/core/middleware.py` (`RequestIDMiddleware`) |
| Health | `/api/v1/health`, `/api/v1/health/detailed` | `backend/app/api/endpoints/health.py` |
| Compose probes | service `healthcheck` entries | `docker-compose.yml` |
| Scrape config | `docker/prometheus/prometheus.yml` → `prometheus:9090` | `docker/prometheus/prometheus.yml` |

---

## 2. Metrics (Prometheus)

`ENABLE_METRICS=true` (default) installs `PrometheusMiddleware` as the outermost middleware. Counters/histograms:

- `codesense_http_requests_total` — HTTP requests by method/path/status
- `codesense_http_request_duration_seconds` — request latency
- `codesense_ingestion_*_total` — ingestion events (received/processed/failed/dupes)
- `codesense_worker_*_total / _seconds` — Celery job counts and duration
- `codesense_db_query_duration_seconds` — DB query latency
- `codesense_cache_hits_total` — cache hits/misses

Scrape target:

```text
http://<host>:8000/metrics
```

Prometheus itself runs at `http://localhost:9090` (Compose), scraping the backend per `docker/prometheus/prometheus.yml`. Metrics are disabled when `prometheus_client` is not installed (`METRICS_ENABLED = False`); `/metrics` then returns a JSON `metrics_disabled` response.

---

## 3. Tracing (OpenTelemetry)

Enabled with `ENABLE_TRACING=true` and `OTEL_EXPORTER_OTLP_ENDPOINT` set. `setup_tracing()` in `backend/app/core/observability.py` configures a `TracerProvider` with a console exporter by default and an OTLP exporter when an endpoint is configured. Tracing is a no-op if OpenTelemetry packages are missing.

---

## 4. Logging

`setup_logging()` (called at import in `main.py`) initializes logging. `RequestIDMiddleware` generates/propagates `X-Request-ID` and logs every request with method, path, status, and duration. Logs are available via:

```bash
docker compose logs -f backend
```

---

## 5. Health checks

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/health` | DB connectivity + internet/AI mode |
| `GET /api/v1/health/detailed` | DB, Redis, worker stats, metrics, internet/AI mode |
| `GET /metrics` | Prometheus scrape target |
| Compose `healthcheck` | postgres `pg_isready`, redis `ping`, backend `/api/v1/health`, nginx `/health` |

Detailed health reports worker stats (`jobs_processed`, `jobs_failed`, `last_run_at`, `healthy`) via `backend/app/worker/base.py::get_worker_stats`.

---

## 6. Verification

- `tests/integration/test_observability.py` — observability behavior (metrics, tracing setup)
- `tests/unit/test_infrastructure.py` — metrics module import, `PrometheusMiddleware` ASGI lifecycle, health endpoint infra checks, `/metrics` endpoint
- `curl -f http://localhost/api/v1/health/detailed` — confirms DB, Redis, worker status
