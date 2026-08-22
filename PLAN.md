# CodeSense — Development PLAN.md

**Status:** Draft (living document — check off items as they complete)
**Last updated:** August 19, 2026
**Source docs:** `docs/` — PRD, TRD, Implementation Plan, Application Flow, Backend Schema

---

## 1. What We Are Building

CodeSense is a **privacy-preserving, provider-agnostic engineering analytics platform** that collects software-development activity from many tools (Git, issue trackers, CI/CD, deployments, incidents), stores the raw events **unmodified**, normalizes them into a **canonical analytical model**, and turns them into **team-level engineering insights** — an explainable **Engineering Health Score**, bottleneck detection, anomaly detection, trend analysis, dashboards, and optional AI explanations.

> The goal is to measure **engineering-system health**, never to rank or surveil individual developers.

### These are the LOCKED principles (non-negotiable)

1. Raw provider events are stored **untouched** (immutable).
2. Analytics operate on a **canonical layer**, never directly on a provider schema → provider-agnostic.
3. **No individual productivity / performance / ranking scores** — ever.
4. **Developer identity is never sent to cloud LLMs** (AI privacy gateway).
5. **Core analytics work offline** (no Internet required).
6. **Cloud AI is optional** and degrades gracefully (falls back to rule/metric explanations).
7. The **Engineering Health Score is team-level and explainable** (Score → Dimension → Metric → Evidence).
8. The **real-time simulator is a data source**, not the product itself.
9. Provider connectors are **modular** and replaceable.

---

## 2. Target Architecture

```
Engineering Sources (Git / Issues / CI-CD / Deploy / Incidents)
        │
        ▼
Connector Layer  (Provider Adapters → validation)
        │
        ▼
Ingestion Service  (REST API │ Webhook │ Batch │ Simulator)
        │
        ▼
Raw Event Store  (immutable provider events)
        │
        ▼
Normalization / Mapping Layer  (Provider event → Canonical event)
        │
        ▼
Canonical Data Layer  (teams, repos, work_items, changes, reviews,
                        builds, deployments, incidents, canonical_events)
        │
        ├──────────────┬───────────────┬───────────────┐
        ▼              ▼               ▼               ▼
  Metric Engine   Health Score    Trend Engine   Anomaly/Bottleneck
        │              │               │               │
        └──────────────┴───────┬───────┴───────────────┘
                               ▼
                     Insight / Recommendations
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
            Dashboards & API      Optional AI Explanation
                                   (Privacy Gateway → LLM)
```

**Dependency rule:** Never skip ahead. The build order is strictly chronological:
`Data foundation → ingestion → canonical model → analytics → Health Score → detection → UI → AI → integrations → testing → deployment.`

---

## 3. Technology Stack

| Layer | Choice | Notes |
|---|---|---|
| Backend | **Python + FastAPI** (Uvicorn, Pydantic) | Async, validation, ML-friendly |
| ORM / Migrations | **SQLAlchemy + Alembic** | Versioned schema migrations |
| Database | **PostgreSQL** | Layered schemas: `raw`, `core`, `analytics`, `configuration`, `audit` |
| Data processing | **Pandas / NumPy** (Polars optional) | Metric & aggregation engine |
| Cache / queue | **Redis** (optional for MVP) | Caching, queues, rate limiting (deferred, DB is sufficient for MVP) |
| Frontend | **React + TypeScript** (+ Recharts/Plotly) | Strict standard; React + TS only (no Streamlit) |
| AI | **OpenRouter-compatible LLM** (optional) | Behind privacy gateway |
| Infra | **Docker + Docker Compose** (+ Nginx optional) | Reproducible deploy |

---

## 4. Repository Structure

```
codesense/
├── backend/
│   └── app/
│       ├── main.py
│       ├── core/          # config, logging, security, db
│       ├── api/           # routers: /events, /teams, /metrics, /health-score, ...
│       ├── models/        # SQLAlchemy models
│       ├── schemas/       # Pydantic schemas
│       ├── services/      # business logic (metrics, health, insights)
│       ├── repositories/  # data access
│       ├── connectors/    # provider adapters (github, gitlab, jira, simulator)
│       ├── ingestion/     # validation, dedup, raw storage
│       ├── normalization/ # provider → canonical mappers
│       ├── metrics/       # metric engine
│       ├── health_score/
│       ├── anomaly_detection/
│       ├── insights/
│       ├── privacy/       # privacy gateway, AI sanitizer
│       └── ai/            # optional LLM client
├── frontend/              # React/TS app
├── simulator/             # standalone external simulator (strictly outside the backend)
├── database/              # migrations (Alembic), seed data
├── tests/                 # unit, integration, privacy, offline, e2e
├── docs/                  # architecture, api, metrics, privacy, deployment, ...
├── scripts/               # dev/ops helper scripts
├── docker/                # Dockerfiles & compose
├── .env.example
├── .gitignore
└── README.md
```

---

## 5. Database Schema (PostgreSQL)

```
raw/        provider_events              ← immutable original payloads
core/       organizations, teams, repositories, projects, work_items,
            changes, reviews, builds, deployments, incidents, canonical_events
analytics/  metric_definitions, metric_values, health_scores,
            health_score_components, engineering_trends, analytics_snapshots, ai_insights, ai_insight_requests
configuration/ providers, connector_configs, health_score_configs
audit/      audit_logs
```

### Key rules
- `raw.provider_events` — `payload` **JSONB, never modified**; `UNIQUE(provider, external_event_id)` for idempotency/dedup.
- `core.canonical_events` — the cross-provider event spine: `event_type`, `occurred_at`, `organization_id`, `team_id`, `project_id`, `repository_id`, `entity_type`, `entity_id`, `actor_ref`, `metadata`.
- `actor_ref` (developer ref) may exist internally for integrity/authz but **must be stripped before any LLM payload (applies to both Cloud and Local LLMs)**.
- **Forbidden** columns/metrics: `developer_productivity_score`, `developer_performance_score`, `developer_rank`, `developer_efficiency_score`.
- Provider credentials never stored in `connector_configs` — use env vars / secrets manager.
- Index priority: `provider+external_id`, `(organization_id, team_id, project_id, occurred_at)`, `(repository_id, occurred_at)`, `(event_type, occurred_at)`.

---

## 6. Canonical Event Types

```
WORK_ITEM_CREATED | WORK_ITEM_STARTED | WORK_ITEM_COMPLETED
CHANGE_CREATED | CHANGE_UPDATED | CHANGE_MERGED | CHANGE_CLOSED
REVIEW_REQUESTED | REVIEW_STARTED | REVIEW_COMPLETED
BUILD_STARTED | BUILD_COMPLETED | BUILD_SUCCEEDED | BUILD_FAILED
DEPLOYMENT_STARTED | DEPLOYMENT_COMPLETED | DEPLOYMENT_FAILED | DEPLOYMENT_ROLLED_BACK
INCIDENT_CREATED | INCIDENT_ACKNOWLEDGED | INCIDENT_RESOLVED
```

Example mapping (proves provider-agnosticism):
- GitHub `pull_request.opened` → `CHANGE_REVIEW_REQUESTED`
- GitLab `merge_request.created` → `CHANGE_REVIEW_REQUESTED`

---

## 7. MVP Metrics (12)

| Category | Metric | Formula (concept) |
|---|---|---|
| Delivery | Deployment Frequency | successful deployments / period |
| Delivery | Lead Time for Changes | deployment_time − change_start_time |
| Delivery | Cycle Time | completion_time − work_start_time |
| Development | PR/MR Cycle Time | merge_time − creation_time |
| Development | Review Turnaround | review_completion − review_request |
| Development | Review Backlog | # changes awaiting review in period |
| CI/CD | Build Success Rate | successful_builds / total_builds |
| CI/CD | Pipeline Duration | completion_time − start_time |
| Deployment | Deployment Failure Rate | failed_deployments / total_deployments |
| Reliability | Change Failure Rate | failed_changes / total_changes |
| Reliability | MTTR | incident_resolution − incident_start |
| Workflow | Work-in-Progress | active in-flight work in period |

Aggregations: hourly / daily / weekly / monthly / custom range, at team and repository level, with baseline + % change.

---

## 8. Engineering Health Score

- **Team-level** composite of **6 dimensions**:
  | Dimension | Default weight |
  |---|---:|
  | Delivery Flow | 20% |
  | Development Flow | 20% |
  | Review Flow | 15% |
  | CI/CD Reliability | 15% |
  | Deployment Health | 15% |
  | Operational Health | 15% |
- Each raw metric is normalized to a **0–100 dimension score** → weighted → overall **0–100**.
- **Weights must remain configurable** (`configuration.health_score_configs`).
- **Explainable:** every score traces Score → Dimension → Metrics → Evidence.
- Stores `previous_score` + `score_change` for trend comparison.

---

## 9. Detection & Insights

### Bottlenecks (categories: REVIEW, CI, DEPLOYMENT, WORKFLOW, INCIDENT)
- **Review:** backlog ↑ **and** turnaround ↑
- **CI:** pipeline duration ↑ **or** failure rate ↑
- **Deployment:** deployment failure ↑ **or** rollback rate ↑
- **Workflow:** WIP ↑ **and** cycle time ↑

### Anomalies
Start with statistical baseline methods: **rolling averages (7/30-day), % change, Z-score, baseline comparison**. Record `baseline`, `observed_value`, `change_percent`, `severity (LOW/MED/HIGH/CRITICAL)`, `confidence`.

### Insights (`analytics.insights`)
Rule-based first. Each insight: `type`, `category`, `severity`, `title`, `description`, `evidence` (linked metrics), `generated_by (RULE_ENGINE / STATISTICAL_ENGINE / LOCAL_AI / CLOUD_AI)`. Lifecycle: Detected → Active → Reviewed → Resolved → Archived.

---

## 10. REST API (prefix `/api/v1`)

| Endpoint | Purpose |
|---|---|
| `GET /health` | health probe |
| `POST /events`, `POST /events/batch`, `GET /events` | Ingestion (raw events) |
| `POST /webhooks/{provider}` | Webhook receiver |
| `GET /organizations`, `GET /organizations/{id}` | Organizations |
| `GET /teams`, `GET /teams/{id}` | Teams |
| `GET /projects`, `GET /projects/{id}` | Projects |
| `GET /metrics` | Metric Definitions (metadata) |
| `GET /metrics/{metric_id}/values` | Get actual aggregated metric data values (supports filtering by organization_id, team_id, project_id, repository_id, occurred_after, occurred_before) |
| `GET /health-score` | Get engineering health scores (supports filtering by organization_id, team_id, project_id, repository_id) |
| `GET /insights` | Get engineering/AI insights |
| `GET /anomalies` | Get detected anomalies |
| `GET /bottlenecks` | Get detected flow bottlenecks |
| `POST /ai/explain` | Generate synchronous real-time AI explanation (receives aggregates, strips identity, queries LLM) |

Standardized error responses: 400 / 401 / 403 / 404 / 409 / 422 / 500.

---

## 11. Implementation Phases

Each phase lists **Tasks** (checkboxes) and a **Definition of Done (DoD)** — do not start the next phase before the DoD passes.

### Phase 0 — Project Definition ✅ (docs are the deliverable)
- [x] PRD, TRD, Backend Schema, Application Flow, Implementation Plan authored
- [x] ⇠ Confirm MVP scope / metrics / score weights / privacy / offline / provider strategy
- [x] Initialize Git repository

### Phase 1 — Development Environment ✅
- [x] Scaffold repo structure (backend/frontend/simulator/database/tests/docs/scripts/docker)
- [x] Python venv + FastAPI, Uvicorn, Pydantic, SQLAlchemy, Alembic, psycopg, pytest
- [x] `.env.example`, `.gitignore`, `README.md`
- **DoD:** Backend starts with working `GET /api/v1/health`.

### Phase 2 — Database Foundation ✅
- [x] PostgreSQL up; create `codesense` DB
- [x] Create schemas (`raw`, `core`, `analytics`, `configuration`, `audit`) + all tables
- [x] Alembic initial migration; verify migrate **and** rollback
- [x] Add required indexes
- **DoD:** Full schema created from a clean DB via migrations only.

### Phase 3 — Backend Foundation ✅
- [x] App structure (core/api/models/schemas/services/repositories)
- [x] Env, DB, logging, settings config
- [x] SQLAlchemy models + session + repository pattern + transactions
- [x] Standard error handling
- **DoD:** FastAPI ⇄ PostgreSQL round-trip with reliable responses.

### Phase 4 — Real-Time Simulator (data source; NOT the product) ✅
- [x] Entity generators: orgs, teams, repos, projects, work_items, changes, reviews, builds, deployments, incidents
- [x] Event generators for all canonical events
- [x] Scenarios (sequential): NORMAL → HIGH_LOAD → REVIEW_BOTTLENECK → CI_BOTTLENECK → DEPLOYMENT_FAILURE → INCIDENT_SPIKE → RECOVERY
- [x] Controls: START / STOP / PAUSE / RESUME / STATUS / SCENARIO
- [x] Deterministic when seeded; realistic timestamps; **sends through the real ingestion API** (never bypasses pipeline)
- **DoD:** Simulator streams realistic, correlated events continuously.

### Phase 5 — Ingestion Pipeline ✅
- [x] `POST /events`, `/batch`, `GET /events`
- [x] Validation: provider, event id, event type, timestamp, payload, source
- [x] Dedup via `provider + external_event_id` (idempotency)
- [x] Raw storage with `processing_status` (PENDING/PROCESSING/PROCESSED/FAILED)
- [x] Quarantine / dead-letter for invalid events
- **DoD:** Thousands of simulated events ingested reliably, no duplicates.

### Phase 6 — Canonical Data Layer ✅
- [x] Normalization framework (`base.py`, `github.py`, `gitlab.py`, `jira.py`, `simulator.py`)
- [x] Provider→canonical mappings (PR/MR → `CHANGE_CREATED`, review → `REVIEW_COMPLETED`, …)
- [x] Canonical entity creation + relationship resolution (Team→Repo→Change→Review→Build→Deploy→Incident)
- [x] `actor_ref` handling (internal only)
- **DoD:** Different provider-shaped events converge to the same canonical model.

### Phase 7 — Analytics / Metric Engine
- [ ] Generic metric framework (definition → query → calc → aggregate → `metric_values`)
- [ ] Delivery → Development → CI/CD → Reliability metrics (12 above)
- [ ] Time aggregations + baselines + % change
- **DoD:** All MVP metrics compute correctly from canonical events.

### Phase 8 — Engineering Health Score
- [ ] 6 dimensions, normalization to 0–100, configurable weights
- [ ] Weighted overall score
- [ ] Explainability (Score→Dimension→Metric→Evidence)
- [ ] Historical score + change
- **DoD:** Reproducible, explainable, team-level score.

### Phase 9 — Bottleneck & Anomaly Detection
- [ ] Review / CI / Deployment / Workflow bottleneck detection (rule conditions above)
- [ ] Anomaly detection: rolling averages, % change, Z-score, baseline comparison
- [ ] Severity (LOW/MEDIUM/HIGH/CRITICAL) + evidence stored with each detection
- **DoD:** Simulator bottleneck scenarios automatically produce the expected detections.

### Phase 10 — Insights Engine
- [ ] Rule-based insights (e.g., backlog ↑ + turnaround ↑ ⇒ “Review flow is becoming a bottleneck”)
- [ ] Insight structure + lifecycle (Detected→Active→Reviewed→Resolved→Archived)
- **DoD:** CodeSense auto-explains significant changes via deterministic rules.

### Phase 11 — Frontend Foundation
- [ ] React+TS app: routing, API client, shared UI
- [ ] Layout: sidebar, header, team selector, time-range selector, main content, user menu
- [ ] Navigation (Overview, Health, Delivery, Development, CI/CD, Reliability, Insights, Anomalies, Bottlenecks, Trends, Integrations, Simulator, AI Analysis, Settings)
- **DoD:** Navigate all major sections.

### Phase 12 — Dashboards
- [ ] Overview (score, change, dimension scores, delivery/devel/CI-CD/reliability summaries, active bottlenecks/anomalies, latest insights)
- [ ] Health dashboard (score → components → trend → contributing metrics → evidence)
- [ ] Delivery, Development, CI/CD, Reliability, Insights dashboards with drill-down
- **DoD:** User can operate CodeSense end-to-end on simulator data.

### Phase 13 — AI Intelligence Layer (ONLY after deterministic analytics work)
- [ ] Privacy gateway: strip names/emails/usernames/IDs, exclude raw payloads + individual metrics, validate payload (strictly enforced for both Cloud and Local LLMs)
- [ ] Use cases in order: score explanation → anomaly explanation → bottleneck explanation → trend summary → investigation suggestions
- [ ] Synchronous real-time generation (blocks request until LLM replies, no async background job queue needed for MVP)
- [ ] OpenRouter-compatible model; graceful failure fallback to structured insights
- **DoD:** AI explains team-level analytics **without receiving any developer identity**.

### Phase 14 — Privacy & Offline Mode
- [ ] Privacy audit (no individual scores/rankings, restricted raw access)
- [ ] Small-team controls: min aggregation thresholds, restricted drill-down, RBAC, masking
- [ ] Internet-available → Normal; unavailable → Offline (core keeps working, AI unavailable)
- **DoD:** Core analytics operate with no Internet; UI clearly marks AI offline.

### Phase 15 — Real Provider Integrations (only after simulator validates the whole pipeline)
- [ ] First provider: **GitHub** → GitLab → Jira → CI/CD
- [ ] Per provider: auth, API client, pagination, rate limits, event retrieval, webhooks, mapping, errors, sync state
- [ ] Cross-provider test: equivalent events from GitHub & GitLab → same canonical type
- **DoD:** Analytics work identically regardless of provider.

### Phase 16 — Authentication & RBAC
- [ ] Auth, sessions/tokens, org & team-level scoping
- [ ] Roles: ADMIN / ENGINEERING_LEADER / ENGINEERING_MANAGER / TECH_LEAD / ANALYST / DEVELOPER
- [ ] Protect APIs + dashboard routes
- **DoD:** Users only see data their role/team permits.

### Phase 17 — Testing & Validation
- [ ] Unit: validation, dedup, normalization, metrics, health score, anomaly/bottleneck, privacy filtering
- [ ] Integration: Simulator→Ingestion→Raw→Canonical→Analytics→Dashboard
- [ ] Privacy: attempt to send name/email/ID/individual metrics → expect REQUEST BLOCKED
- [ ] Offline: disable Internet → metrics/score/dashboard/history OK, cloud AI unavailable
- [ ] Scenarios (NORMAL, REVIEW_BOTTLENECK, CI_BOTTLENECK, DEPLOYMENT_FAILURE, INCIDENT_SPIKE, RECOVERY)
- [ ] Performance: ingestion rate, API latency, DB queries, dashboard load, analytics latency
- **DoD:** All critical tests pass.

### Phase 18 — Deployment
- [ ] Docker services: `codesense-api`, `codesense-worker` (optional), `codesense-simulator`, `postgres`, `codesense-dashboard`, `nginx` (Redis optional/deferred, DB is sufficient for MVP)
- [ ] `docker-compose.yml`: networking, volumes, env, health checks, restart policies
- [ ] DB persistence across restarts; logging; backup/restore
- **DoD:** Deploy from scratch; restart without data loss.

### Phase 19–21 — Observability, Security Hardening, Documentation
- [ ] Metrics/logs: API (count/latency/errors), ingestion (received/processed/failed/dupes), DB, analytics, connectors
- [ ] Security: no hard-coded secrets, authz validation, rate limiting, input validation, SQLi/XSS/CSRF review, secret-leak review, AI identity-leak review
- [ ] Docs: architecture, backend-schema, api, simulator, metrics, health-score, privacy, offline-mode, integrations, deployment, testing, troubleshooting + README
- **DoD:** No critical security issues; system is documented & observable.

### Phase 22 — Final End-to-End Validation (7 tests)
1. Normal engineering → stable score
2. Review bottleneck → score ↓, bottleneck + insight generated
3. CI bottleneck → CI reliability ↓, score ↓, CI bottleneck detected
4. Deployment incident → rollback, incident, MTTR, operational health ↓
5. Recovery → metrics return to baseline, score recovers
6. AI explanation → sanitized payload → explanation
7. Offline → core works, AI unavailable
- **DoD:** All seven scenarios work correctly.

### Phase 23 — Final Demonstration (18-step scripted walkthrough)
Open app → architecture → start simulator → normal activity → health score → switch to review bottleneck → live metric changes → score drops → open bottlenecks → open detected review bottleneck → show evidence → AI explanation → show privacy-safe payload → disable Internet → core still works → AI unavailable → switch to recovery → score recovers.

---

## 12. Definition of Done (MVP-complete)

The complete workflow runs without manual intervention:

```
Real-Time Simulator → Ingestion API → Immutable Raw Data → Canonical Data
→ Analytics Engine → Engineering Health Score → Anomaly & Bottleneck Detection
→ Insights Engine → CodeSense Dashboard → Optional AI Explanation
```

### MVP acceptance highlights (from PRD §37)
- **Data:** simulator generates realistic events; ingestion continuous; raw events unchanged; dedup works; canonical transform works.
- **Analytics:** core metrics correct; team aggregation; historical trends; health score generated & explainable.
- **Privacy:** no individual productivity scores; cloud AI has no developer identity; access controlled; small-team risks considered.
- **Intelligence:** bottlenecks + basic anomalies detected; AI explanations from sanitized aggregates; AI failure doesn’t break core.
- **Offline:** core analytics, historical data, and health score work offline; cloud AI clearly marked unavailable.
- **Provider-agnostic:** analytics on canonical events; a 2nd provider adds without rewriting the metric engine.

**Performance targets (prototype):** health <200 ms · normal API <500 ms · ingestion ack <1 s · dashboard query <2 s · simulator→analytics <5 s · score recalc <5 s. Scale floor: 10 teams / 50 repos / 100k+ events without architectural change.

---

## 13. Non-Goals (explicitly OUT of MVP)

- No individual developer ranking / productivity scores.
- No surveillance or autonomy over people decisions (employment/promotion/compensation).
- No dependency on cloud AI; no sending developer identity to LLMs.
- No modifying raw provider events.
- No replacing Git/CI-CD/issue/incident tools.
- Not all providers in MVP — start with simulator, then GitHub, then others.

---

## 14. Top Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Provider-agnosticism drift (metrics coupled to one provider) | Enforce canonical layer; never let metric engine touch raw payloads; cross-provider test (Phase 15.4) |
| Privacy leakage to AI | Privacy gateway with PII detection + hard block; privacy tests that expect REQUEST BLOCKED (Phase 17.3) |
| AI failure breaking core | Strict separation; AI is a leaf branch off analytics; timeout + fallback (Phase 13/TRD §45) |
| Simulator bypassing real pipeline | Simulator posts through `/api/v1/events` only; never direct DB writes (Phase 4/TRD §20.2) |
| Offline regression | Dedicated offline test suite (Phase 17.4) |
| Non-explainable score | Score→Dimension→Metric→Evidence chain enforced in schema + UI (Phase 8/12) |
| Scope creep (jumping to AI/dashboards/providers early) | Chronological phase gates with DoD per phase |

---

## 15. Suggested Next Actions

1. **Execute Phase 0**: confirm MVP scope + metric list + score weights + provider strategy; `git init`.
2. **Stand up Phase 1–2**: scaffold repo, local env, PostgreSQL via Docker, Alembic baseline.
3. Build **Phase 4–5** (simulator + ingestion) early — everything downstream depends on reliable event flow.

---
*Generated from `docs/CodeSense — PRD`, `— TRD`, `— Implementation Plan`, `— Application Flow`, and `— Backend Schema`. Updated as work progresses.*
