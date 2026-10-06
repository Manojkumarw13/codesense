# Phase 18 — Dashboard Implementation Spec

## Problem Statement

Phase 17 shipped navigation with placeholder pages ("wires up in Phase 18"). Users can move between sections but see no real CodeSense analytics — no health score, no bottlenecks/anomalies/insights, no trends. The product is not yet operable on simulator data.

## Solution

Connect the existing pages to the real `/api/v1/*` list endpoints with loading/empty/error states, team+time context display, severity filtering, evidence drill-down, and dependency-light SVG charts (score trend sparkline, dimension bars). DoD: a user can operate CodeSense end-to-end on simulator-generated data through the dashboard.

## User Stories

1. As an engineering leader, I want the Overview to show the latest health score + change, so that I see team health at a glance.
2. As an engineering leader, I want the Overview to show active bottleneck/anomaly/insight counts, so that I know what needs attention.
3. As an engineering leader, I want the Health page to show score → dimensions → evidence, so that I can explain any score.
4. As an engineering leader, I want a score trend chart, so that I can see recovery vs degradation over time.
5. As a developer, I want Delivery/Development/CI-CD/Reliability pages to show the relevant dimension slice + related signals, so that each flow area is inspectable even before a metric-values endpoint exists.
6. As a user, I want severity/category filters on Insights/Anomalies/Bottlenecks, so that I can cut noise.
7. As a user, I want evidence drill-down on every detection, so that Score → Dimension → Metric → Evidence stays explainable.
8. As a user, I want clear empty states ("no data — run the simulator"), so that a fresh DB is not confusing.
9. As a user, I want API failures to render as error states, not blank pages, so that offline backend is obvious.
10. As a developer, I want one `useApi` data-fetch seam, so that Phase 19+ pages reuse loading/error handling.
11. As a privacy reviewer, I want no developer identity rendered anywhere, so that the team-level-only principle holds.
12. As an operator, I want `npm run build` green with no new runtime deps, so that the Docker image stays lean.

## Implementation Decisions

- Modules to build under `frontend/src/`: `hooks/useApi.ts` (single fetch seam returning `{data, loading, error}`), `components/charts/ScoreTrend.tsx` (SVG sparkline of score history) and `DimensionBars.tsx` (SVG bars from `component_metrics`), `components/Evidence.tsx` (`<details>` JSON drill-down), updated `api/client.ts` (fix: drop broken `/metrics` JSON + `/metrics/{id}/values` calls that 404 since backend `/metrics` is Prometheus text; add `{items}` unwrapping, detail getters, optional UUID filters never sent with placeholder team names).
- Interfaces: list endpoints return `{total, skip, limit, items}` — client unwraps to arrays. Field truth per `backend/app/models/analytics.py`: HealthScore has `score, previous_score, score_change, component_metrics, period_start/end, calculated_at`; Insight has `insight_type, category, severity, title, content, confidence, evidence, generated_by, status`; Anomaly has `severity, baseline_value, observed_value, change_percent, confidence, evidence, detected_at`; Bottleneck has `category, severity, title, description, evidence, detected_at`.
- Team scoping: pages display the selected team name from `AppContext` but do NOT send placeholder names as UUID filters (backend would 422); UUID filtering activates in Phase 21/22 with real team IDs.
- Pages wired: Overview (latest score + counts + trend), Health (latest score, dimensions, history table), Delivery/Development/CI-CD/Reliability (dimension slice + related insights/anomalies/bottlenecks), Insights/Anomalies/Bottlenecks (filterable lists + evidence), Trends (score history chart + table). Integrations/Simulator/AI/Settings stay placeholders (Phase 19/21 scope).
- Styling: extend existing `styles.css` (tables, filters, charts, evidence); no Tailwind, no Recharts/Plotly in this phase.
- No backend changes in this phase; no auth changes; no metric-values endpoint (noted as future backend gap if needed).

## Testing Decisions

- What makes a good test: external behavior at the highest seam — pages render loading → data/empty/error; client unwraps `{items}`; charts render with empty input without crashing — not CSS internals.
- Modules to test: `apiClient` unwrap logic, `useApi` states, route smoke (all routes still resolve). Verified in this phase by `tsc --noEmit` + `vite build` + a Node smoke script asserting dashboard wiring (imports of useApi/charts in pages, no `/metrics/{id}` calls). Full Vitest + Playwright deferred to Phase 23.
- Prior art: Phase 17 build-gate + smoke script; backend `pytest` + `httpx` integration tests in `tests/`.

## Out of Scope

Real metric-value charts (needs backend endpoint — future gap), drill-down routing to single-item pages (lists + evidence suffice), LLM explainer UI (Phase 19), provider integrations UI (Phase 21), auth/RBAC (Phase 22), Vitest/Playwright suites (Phase 23).

## Further Notes

- Backend CORS already open (`backend/app/main.py:41`); dev proxy covers `/api`.
- Empty DB is the normal first-run state: every wired page must handle zero items with a "run the simulator" hint.
