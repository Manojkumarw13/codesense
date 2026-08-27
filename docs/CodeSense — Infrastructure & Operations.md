# CodeSense — Infrastructure & Operations

**Document Status:** Living Document  
**Version:** 1.0  
**Project:** CodeSense  
**Purpose:** Define the infrastructure, operational components, technology stack, and architectural rules for CodeSense.

---

## 1. Infrastructure Goals

The goal is to make CodeSense **fast, reliable, secure, scalable, and easy to maintain**.

---

## 2. Core Architecture Pipeline

```text
Data Sources
     ↓
API / Webhooks
     ↓
Validation + Deduplication
     ↓
Raw Events
     ↓
Canonical Events
     ↓
Background Workers
     ↓
Metrics
     ↓
Rules + Statistics + ML (FusionEngine)
     ↓
Evidence + Confidence
     ↓
LLM / Agents
     ↓
Insights
     ↓
Dashboard / Alerts
```

---

## 3. The 8 Components

| # | Component | Purpose |
|---|---|---|
| 1 | **PostgreSQL** | Main permanent database (Source of truth) |
| 2 | **Redis** | Cache + job queue |
| 3 | **Background Workers** | Process events, analytics, and ML tasks asynchronously |
| 4 | **Data Validation** | Prevent bad/duplicate data |
| 5 | **Observability** | Logs, metrics, tracing, health checks |
| 6 | **Security** | Authentication, RBAC, tenant isolation, AI data boundary |
| 7 | **Backups & Recovery**| Protect against data loss |
| 8 | **CI/CD** | Automatically test and deploy changes |

---

## 4. Recommended Technology Stack

```text
Frontend        → React / Next.js
API             → FastAPI
Database        → PostgreSQL
Cache           → Redis
Workers         → Celery / RQ / Arq
ML Layer        → Scikit-learn, XGBoost, Prophet
Containers      → Docker
Metrics         → Prometheus
Dashboards      → Grafana
Tracing         → OpenTelemetry
Testing         → Pytest + Hypothesis
Linting         → Ruff
Type checking   → MyPy
```

---

## 5. The 10 Operational Rules

**LOCKED RULES (Non-negotiable - Enforced in AGENTS.md):**

1. **PostgreSQL is the source of truth.**
2. **Never modify raw provider events.**
3. **Make ingestion idempotent so duplicate events don't create duplicate data.**
4. **Security must be enforced by code, not just AI prompts.**
5. **CodeSense should continue working when the LLM or Internet is unavailable.**
6. **Start simple, don't over-engineer infrastructure** (No Kubernetes, Kafka, or microservices initially).

**FLEXIBLE GUIDELINES:**

7. **Don't calculate everything inside API requests.** Use background workers.
8. **Pre-compute expensive metrics.**
9. **Every important output must have:** Value, Confidence, Data Quality, Freshness, Formula Version. (Evidence + Confidence is mandatory).
10. **Monitor the infrastructure itself**, not just the engineering metrics.

---

## 6. Ideal Foundation

Build the **infrastructure first, intelligence second**. If the data pipeline, database, processing, security, and observability are strong, the rest of CodeSense becomes much easier to scale and improve.

```text
        FastAPI
           │
    ┌──────┴──────┐
    │             │
PostgreSQL      Redis
    │             │
    │          Workers
    │             │
    └──────┬──────┘
           ↓
    Canonical Data
           ↓
       Analytics
           ↓
 Rules + Stats + ML (FusionEngine)
           ↓
    Evidence Layer
           ↓
      LLM / Agents
```
