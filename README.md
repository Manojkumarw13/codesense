# CodeSense

CodeSense is an ML-powered engineering intelligence platform that preserves privacy and remains provider-agnostic. It collects software development activity from various systems, normalizes it into a canonical analytical model, and calculates team-level engineering insights (such as an explainable Engineering Health Score, hybrid ML anomaly detection, risk prediction, bottleneck detection, trend analysis, and dashboards).

## Key Principles
1. Raw provider events are stored unmodified (immutable).
2. Analytics operate on a canonical layer (provider-agnostic).
3. No individual developer productivity scoring.
4. Developer identity is stripped before sending to any LLM.
5. Core analytics work offline.

## Project Structure
- `backend/`: Python + FastAPI backend application.
- `frontend/`: React + TypeScript frontend dashboard.
- `simulator/`: External standalone data simulator.
- `database/`: Database migrations (Alembic) and schemas.
- `docker/`: Docker Compose configurations.
- `docs/`: Technical specifications and requirements.

## Quick Start (Docker)

```bash
cp .env.example .env          # edit SECRET_KEY before production
docker compose up -d --build  # backend, postgres, redis, worker, nginx, prometheus, dashboard
curl http://localhost/health  # nginx self-check -> "ok"
curl http://localhost/api/v1/health
```

## Operations

- `docker compose logs -f backend` — view backend logs
- `docker compose down` — stop (volumes preserved); `docker compose down -v` — wipe data
- `alembic upgrade head` — apply database migrations
- `scripts/db_backup.sh` / `scripts/db_restore.sh <file>` — backup / restore Postgres

## Documentation

| Doc | File |
|---|---|
| Deployment | `docs/CodeSense — Deployment.md` |
| Observability | `docs/CodeSense — Observability.md` |
| Security Hardening | `docs/CodeSense — Security Hardening.md` |
| Troubleshooting | `docs/CodeSense — Troubleshooting.md` |

## Getting Started
To be updated during implementation.
