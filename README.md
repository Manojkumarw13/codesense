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

## Getting Started
To be updated during implementation.
