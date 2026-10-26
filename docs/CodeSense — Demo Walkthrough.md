# CodeSense — Demo Walkthrough

**Document Status:** Living Document  
**Version:** 1.0  
**Project:** CodeSense  
**Purpose:** 18-step scripted demonstration of the complete CodeSense pipeline, matching PLAN.md Phase 29. Every step maps to real system behavior (endpoints, simulator scenarios, detection rules, privacy gateway, offline probe).

---

## 0. How to run this walkthrough

The demo exercises the real FastAPI backend plus the real-time simulator against a real PostgreSQL database.

| Component | Address | Role |
|---|---|---|
| Backend API | `http://localhost:8000` | API, analytics, detection, health score, AI explain |
| Simulator | `http://localhost:8001` | Event generator, scenario control |
| Database | `localhost:5432` | PostgreSQL (raw, canonical, analytics, core) |

Start both services (e.g. `docker compose up -d` or the local equivalents), then run the steps in order. Steps reference the backend base path `/api/v1` and the simulator control endpoints on port `8001`.

```bash
# Health check (backend)
curl -f http://localhost:8000/api/v1/health

# Simulator control (port 8001)
curl -X POST http://localhost:8001/simulator/start
curl -X POST http://localhost:8001/simulator/scenario -H 'Content-Type: application/json' -d '{"scenario":"NORMAL"}'
```

---

## 1. Open app → architecture

**Action:** Open the CodeSense application and confirm the overall architecture.

**Expected result:** The system is reachable and exposes its architecture: a pipeline from engineering events → canonical data → team-level analytics → Engineering Health Score → bottleneck/anomaly detection → insights → dashboard, with an optional privacy-gated AI layer.

**Verification:**
- `GET http://localhost:8000/api/v1/health` returns healthy.
- Backend OpenAPI: `http://localhost:8000/api/v1/openapi.json` lists all routes (events, health-score, bottlenecks, metrics, ai/explain, ...).
- Architecture reference: `docs/CodeSense — System Architecture.md` and `docs/CodeSense — Application Flow.md` (pipeline: Simulator → Ingestion API → Immutable Raw Data → Canonical Data → Analytics Engine → Health Score → ML Models → Fusion Engine → Insights → Dashboard → Optional AI Explanation).

---

## 2. Start simulator

**Action:** Start the real-time data simulator on the `NORMAL` scenario.

**Expected result:** The simulator begins generating realistic engineering events (work items, changes/PRs, reviews, CI builds, deployments, incidents) and ingesting them into the backend. It first backfills 30 days of historical data, then streams real-time ticks.

**Verification:**
- `POST http://localhost:8001/simulator/start` → `{"message": "Simulator started"}`.
- `GET http://localhost:8001/simulator/status` → `is_running: true`, `current_scenario: "NORMAL"`, backfill progressing.
- `POST http://localhost:8000/api/v1/events/batch` receives events (`ingested_count > 0`).

**Real behavior:** `simulator/main.py` `run_loop()` backfills 30 days × 24 hours, then loops `tick_simulation()` → `send_events_to_backend()` (batch POST to `/api/v1/events/batch`).

---

## 3. Normal activity

**Action:** Let the simulator run on `NORMAL` and confirm normal engineering activity flows through ingestion.

**Expected result:** Events are ingested, deduplicated (re-sent identical events are ignored), and converted into canonical entities (work items, changes, reviews, builds, deployments). Raw provider events are preserved immutably.

**Verification:**
- `GET http://localhost:8000/api/v1/events?provider=simulator` returns ingested events (`total > 0`).
- Re-posting the same `external_event_id` returns `status: "ignored_duplicate"` (idempotent dedup).
- Canonical records exist in the DB (`core.work_items`, `core.changes`, `core.reviews`, `core.builds`, `core.deployments`).

**Real behavior:** `backend/app/api/endpoints/events.py` `ingest_event` / `ingest_events_batch` dedupes by `(provider, external_event_id)` and stores raw `ProviderEvent` rows; `EventProcessor` normalises to canonical entities.

---

## 4. Health score

**Action:** View the Engineering Health Score for the team.

**Expected result:** A team-level Engineering Health Score (0–100) is displayed with component metrics (Delivery Flow, Development Flow, Review Flow, CI/CD Reliability, Deployment Health, Operational Health), the previous score, and the score change. No individual productivity score is shown.

**Verification:**
- `GET http://localhost:8000/api/v1/health-score?team_id=<team_id>` returns an item with `score` in `[0, 100]`, plus `previous_score`, `score_change`, `component_metrics`, `privacy`.
- `privacy.suppressed` is `false` for a normal-sized team (metric evidence visible).

**Real behavior:** `backend/app/api/endpoints/health_score.py` `list_health_scores` / `get_health_score`; `HealthScoreEngine` computes the score per the approved scoring model (team/system-level only, never individual productivity).

---

## 5. Switch to review bottleneck

**Action:** Switch the simulator scenario to `REVIEW_BOTTLENECK`.

**Expected result:** Review completion stalls (`review_completion_chance` drops to 0.02), so pull-request reviews pile up: review backlog and review turnaround both increase.

**Verification:**
- `POST http://localhost:8001/simulator/scenario` body `{"scenario":"REVIEW_BOTTLENECK"}` → `Scenario updated to REVIEW_BOTTLENECK`.
- `GET http://localhost:8001/simulator/status` → `current_scenario: "REVIEW_BOTTLENECK"`.

**Real behavior:** `simulator/main.py` `tick_simulation()` sets `review_completion_chance = 0.02` for `REVIEW_BOTTLENECK`, so reviews remain `PENDING` and backlog/turnaround grow.

---

## 6. Live metric changes

**Action:** Watch metrics change live as the bottleneck scenario runs.

**Expected result:** Review-related metrics move in real time: `review_backlog` and `review_turnaround` change percentages rise above the detection threshold (> 10%). Other dimensions remain near baseline.

**Verification:**
- `GET http://localhost:8000/api/v1/metrics` returns Prometheus metrics (observability endpoint).
- `MetricValue` rows for `review_backlog` / `review_turnaround` show `change_percentage > 10`.
- Health score components reflect the deteriorating Review Flow dimension.

**Real behavior:** `backend/app/api/endpoints/metrics.py` exposes `/api/v1/metrics`; `MetricEngine` calculates `change_percentage` per period; detection thresholds in `backend/app/services/detection.py` `is_increasing(..., threshold=10.0)`.

---

## 7. Score drops

**Action:** Re-check the Engineering Health Score after the review bottleneck has taken effect.

**Expected result:** The overall Engineering Health Score drops (negative `score_change`), driven by the Review Flow component. The score stays within [0, 100] and remains a team-level indicator.

**Verification:**
- `GET http://localhost:8000/api/v1/health-score?team_id=<team_id>` → `score` lower than the baseline from Step 4, `score_change` negative.
- `component_metrics.review_flow` is the weakest dimension.

**Real behavior:** `HealthScoreEngine.calculate_health_score` weights dimensions; review backlog/turnaround increases depress the Review Flow component and thus the aggregate score.

---

## 8. Open bottlenecks

**Action:** Open the bottlenecks list to see detected flow bottlenecks.

**Expected result:** A `REVIEW` category bottleneck is detected (backlog ↑ AND turnaround ↑), with HIGH severity.

**Verification:**
- `GET http://localhost:8000/api/v1/bottlenecks?category=REVIEW` returns at least one item (`total > 0`) with `category: "REVIEW"` and `severity: "HIGH"`.
- No `CI`/`DEPLOYMENT`/`WORKFLOW` bottlenecks expected in this scenario.

**Real behavior:** `backend/app/api/endpoints/bottlenecks.py` `list_bottlenecks`; `DetectionEngine.detect_bottlenecks` fires the REVIEW rule when `review_backlog > 10` AND `review_turnaround > 10`.

---

## 9. Open detected review bottleneck

**Action:** Open the specific detected review bottleneck for its detail view.

**Expected result:** The bottleneck detail shows detection time, severity, category, title, description, affected metrics, and evidence.

**Verification:**
- `GET http://localhost:8000/api/v1/bottlenecks/{bottleneck_id}` returns the REVIEW bottleneck with `evidence.review_backlog_change` and `evidence.review_turnaround_change`, both > 10.

**Real behavior:** `backend/app/api/endpoints/bottlenecks.py` `get_bottleneck` → `serialise_detection`; `Bottleneck.title` "Review Process Bottleneck Detected", `category` "REVIEW".

---

## 10. Show evidence

**Action:** Inspect the evidence behind the detected bottleneck.

**Expected result:** The evidence object quantifies the trigger: review backlog change and review turnaround change percentages, confirming the detection rule fired on real metric movement.

**Verification:**
- Bottleneck `evidence` contains `review_backlog_change` (> 10) and `review_turnaround_change` (> 10).
- Matches `backend/app/services/detection.py` thresholds: `is_increasing("review_backlog")` and `is_increasing("review_turnaround")` with `threshold=10.0`.

---

## 11. AI explanation

**Action:** Request an AI explanation of the health score drop.

**Expected result:** A concise, factual explanation of the score drop is returned, sourced from team-aggregate analytics only. The LLM never sees developer identity.

**Verification:**
- `POST http://localhost:8000/api/v1/ai/explain?use_case=score_explanation&team_id=<team_id>` (online) → `200`, `source: "CLOUD_AI"`, non-empty `explanation`, `sanitized_context` present.
- `sanitized_context` contains no `@` email and no identity keys (`email`, `full_name`, `actor_ref`, `user_id`, `developer`, `author`, `committer`).

**Real behavior:** `backend/app/api/endpoints/ai.py` `explain_analytics` → `explain()`; `build_context` collects only team-aggregate rows (health scores, insights, anomalies, bottlenecks); `PrivacyGateway.sanitize` strips identity before any LLM call; `LlmUnavailableError` falls back to rules.

---

## 12. Show privacy-safe payload

**Action:** Demonstrate the privacy-safe payload sent to AI.

**Expected result:** The `sanitized_context` exposed in the AI response is privacy-safe: team-aggregate data only, developer identity removed, raw provider payloads dropped. Attempting to send identity to the AI is blocked.

**Verification:**
- `sanitized_context` from Step 11 passes the privacy scan: no identity keys, no emails, no `payload`/`raw_payload` blobs.
- Negative check: inserting a `HealthScore` row whose `component_metrics` contains an identity field (e.g. `full_name`) and calling `POST /api/v1/ai/explain` returns `422` with detail containing `REQUEST BLOCKED`.

**Real behavior:** `backend/app/privacy/gateway.py` `PrivacyGateway.sanitize` scans for `IDENTITY_KEYS` (raises `PrivacyBlockedError` → HTTP 422 `REQUEST BLOCKED`) and strips `RAW_KEYS` (`payload`, `raw_payload`, ...). Developer identity never reaches the LLM (see `docs/CodeSense — AI Data Boundary.md`).

---

## 13. Disable Internet

**Action:** Simulate loss of Internet connectivity (offline mode).

**Expected result:** Cloud AI becomes unavailable; the system honestly reports offline and switches to fallback rules. Core analytics are unaffected.

**Verification:**
- Force `InternetState.OFFLINE` (test seam: monkeypatch `get_internet_state` + `reset_connectivity_cache()`), then `GET http://localhost:8000/api/v1/ai/status` → `internet: "offline"`, `mode: "fallback_rules"`.
- AI explain no longer attempts any network/LLM call.

**Real behavior:** `backend/app/core/connectivity.py` `probe_internet` / `get_internet_state`; `ai.py` short-circuits to fallback when `internet is not InternetState.ONLINE`.

---

## 14. Core still works

**Action:** Confirm core analytics continue operating without Internet.

**Expected result:** Ingestion, metrics, health score, and historical analytics all keep working — they are purely database-driven and never consult the connectivity probe.

**Verification:**
- `POST http://localhost:8000/api/v1/events/batch` still ingests events (`ingested_count > 0`).
- `GET http://localhost:8000/api/v1/health-score?team_id=<team_id>` returns a valid score (0–100).
- `GET http://localhost:8000/api/v1/metrics` still returns Prometheus metrics.

**Real behavior:** Per `connectivity.py`: "Offline is a state of the cloud AI dependency, not of the core system: metrics, health score and historical analytics never consult this module."

---

## 15. AI unavailable

**Action:** Request an AI explanation while offline.

**Expected result:** AI gracefully degrades to deterministic rule-based fallback: an explanation is still returned, sourced from `FALLBACK_RULES`, with no model and no network call. Core analytics never break.

**Verification:**
- `POST http://localhost:8000/api/v1/ai/explain?use_case=score_explanation&team_id=<team_id>` (offline) → `200`, `source: "FALLBACK_RULES"`, `model: null`, `reason: "internet_unavailable"`, non-empty `explanation`.
- The LLM client is never invoked (offline short-circuit before any network call).

**Real behavior:** `ai.py` returns fallback when offline; `explainer.fallback_explanation` builds a deterministic explanation from aggregates (headline, weakest dimension, open signals).

---

## 16. Switch to recovery

**Action:** Switch the simulator scenario to `RECOVERY`.

**Expected result:** The system returns toward normal: reviews complete quickly (`review_completion_chance` 0.80), build/deploy failure rates drop (0.02), no new incidents, and outstanding incidents/reviews resolve.

**Verification:**
- `POST http://localhost:8001/simulator/scenario` body `{"scenario":"RECOVERY"}` → `Scenario updated to RECOVERY`.
- `GET http://localhost:8001/simulator/status` → `current_scenario: "RECOVERY"`; active reviews/incidents drain down.

**Real behavior:** `simulator/main.py` `tick_simulation()` `RECOVERY` branch: `review_completion_chance = 0.80`, `build_failure_chance = 0.02`, `deploy_failure_chance = 0.02`, `incident_creation_chance = 0.00`, incident resolve chance 0.50.

---

## 17. Score recovers

**Action:** Re-check the health score and bottlenecks during recovery.

**Expected result:** The Engineering Health Score recovers toward baseline, the Review Flow component improves, and no REVIEW/CI/DEPLOYMENT/WORKFLOW bottlenecks remain.

**Verification:**
- `GET http://localhost:8000/api/v1/health-score?team_id=<team_id>` → `score` higher than the bottleneck low, `score_change` positive or stable.
- `GET http://localhost:8000/api/v1/bottlenecks` → no `REVIEW`/`CI`/`DEPLOYMENT`/`WORKFLOW` categories.

**Real behavior:** `DetectionEngine.detect_bottlenecks` no longer fires (deltas return to normal ranges, e.g. `review_backlog`/`review_turnaround` ≈ 5); `HealthScoreEngine` recomputes a higher score.

---

## 18. Wrap-up

**Action:** Conclude the demonstration.

**Expected result:** All 18 steps have been demonstrated end-to-end against the real system, confirming the complete Phase 29 walkthrough: normal activity → health score → review bottleneck → live metric changes → score drop → bottlenecks → evidence → AI explanation → privacy-safe payload → offline → core still works → AI unavailable → recovery → score recovery.

**Verification:**
- The 7 E2E validation scenarios (`tests/integration/test_e2e_validation.py`) pass: normal stable score, review bottleneck (score ↓ + bottleneck + insight), CI bottleneck, deployment incident (rollback + bottleneck), recovery, AI explanation (sanitized payload → explanation; identity → 422 REQUEST BLOCKED), offline (core works, AI unavailable).
- Run: `/home/manoj/Project/CodeSense/.venv/bin/python -m pytest tests/integration/test_e2e_validation.py -q`

---

## Traceability matrix

| Step | Demo action | Real system behavior | Endpoint / feature |
|---|---|---|---|
| 1 | Open app | Architecture + health | `GET /api/v1/health`, OpenAPI |
| 2 | Start simulator | Backfill + real-time event generation | `POST /simulator/start`, `/simulator/status` |
| 3 | Normal activity | Ingestion + dedup + canonical transform | `POST /api/v1/events/batch`, `GET /api/v1/events` |
| 4 | Health score | Team health score (0–100) + components | `GET /api/v1/health-score` |
| 5 | Switch to review bottleneck | Reviews stall, backlog/turnaround ↑ | `POST /simulator/scenario` REVIEW_BOTTLENECK |
| 6 | Live metric changes | `change_percentage` > 10 on review metrics | `GET /api/v1/metrics`, `MetricValue` |
| 7 | Score drops | Review Flow component depresses score | `GET /api/v1/health-score` |
| 8 | Open bottlenecks | REVIEW bottleneck detected (HIGH) | `GET /api/v1/bottlenecks` |
| 9 | Open detected review bottleneck | Bottleneck detail + evidence | `GET /api/v1/bottlenecks/{id}` |
| 10 | Show evidence | `review_backlog_change`, `review_turnaround_change` > 10 | `detection.py` thresholds |
| 11 | AI explanation | Sanitized team-aggregate → explanation | `POST /api/v1/ai/explain` CLOUD_AI |
| 12 | Privacy-safe payload | Identity stripped; identity → 422 REQUEST BLOCKED | `PrivacyGateway.sanitize` |
| 13 | Disable Internet | AI offline / fallback_rules | `GET /api/v1/ai/status` offline |
| 14 | Core still works | DB-driven core unaffected by offline | `events`, `health-score`, `metrics` offline |
| 15 | AI unavailable | FALLBACK_RULES explanation, no LLM call | `POST /api/v1/ai/explain` offline |
| 16 | Switch to recovery | Reviews/incidents resolve, failures drop | `POST /simulator/scenario` RECOVERY |
| 17 | Score recovers | Score → baseline, bottlenecks clear | `GET /api/v1/health-score`, `bottlenecks` |
| 18 | Wrap-up | Full pipeline validated | `test_e2e_validation.py` 7 scenarios |
