# Phase 17 — Frontend Foundation Spec

## Problem Statement

Backend analytics (Phases 0–16) are complete and exposed via `GET /api/v1/*`, but `frontend/` is empty. Users have no UI to navigate CodeSense sections (Overview, Health, Delivery, Development, CI/CD, Reliability, Insights, Anomalies, Bottlenecks, Trends, Integrations, Simulator, AI Analysis, Settings). No shared layout, routing, or API client exists.

## Solution

Build the React+TypeScript frontend foundation: Vite app with routing, typed API client covering all backend contracts, and shared layout (Sidebar, Header, Team Selector, Time-Range Selector, Main Content, User Menu). All 14 sections navigate with placeholder content; real charts/data wire-up is Phase 18. DoD: navigate all major sections.

## User Stories

1. As an engineering leader, I want a sidebar with all 14 sections, so that I can reach any CodeSense area in one click.
2. As an engineering leader, I want a header with team selector, so that I can scope the (later) dashboards to my team.
3. As an engineering leader, I want a time-range selector (24h/7d/30d/90d + custom), so that I can scope the (later) dashboards to a period.
4. As a user, I want deep-linkable routes (`/health`, `/delivery`, …), so that I can bookmark/share a section.
5. As a user, I want to see backend health status in the UI, so that I know if the API is reachable.
6. As a developer, I want a typed `apiClient` for every `/api/v1/*` endpoint, so that Phase 18 dashboards never touch raw fetch shapes.
7. As a developer, I want shared UI primitives (Card, Badge, Loading, EmptyState, ErrorState), so that Phase 18 dashboards look consistent.
8. As a developer, I want `npm run dev`, `npm run build`, `npm run preview` to work, so that local + Docker workflows are reproducible.
9. As an operator, I want a `frontend/Dockerfile` (nginx serve of dist), so that Phase 24 can add a `dashboard` service without rework.
10. As a user, I want a responsive layout (sidebar collapses on small screens), so that the app is usable on laptop + tablet.
11. As a user, I want graceful API failure (error state, not blank page), so that offline backend is obvious.
12. As a privacy reviewer, I want no developer-identity display anywhere, so that team-level-only principle holds from day one.

## Implementation Decisions

- Modules to build under `frontend/`: `src/app` (router + providers), `src/api/client.ts` (single API seam), `src/components/layout` (Sidebar, Header, TeamSelector, TimeRangeSelector, UserMenu), `src/components/ui` (Card, Badge, Loading, EmptyState, ErrorState), `src/pages/*` (14 placeholders), `src/context/AppContext` (teamId + timeRange global state), `src/types.ts` (backend DTO mirrors).
- Interfaces: `apiClient` wraps `fetch` with `baseUrl = import.meta.env.VITE_API_BASE_URL ?? http://localhost:8000/api/v1`; typed methods: `getHealth`, `getHealthDetailed`, `getMetrics`, `getMetricValues`, `getHealthScore`, `getInsights`, `getAnomalies`, `getBottlenecks`, `getRisk`, `getMlModels`, `getMlFeatures`, `getMlPredictions`, `listEvents`. All return typed JSON, throw `ApiError{status,message}` on non-2xx.
- Routing: `react-router-dom` v6, `BrowserRouter`, routes: `/` (Overview), `/health`, `/delivery`, `/development`, `/cicd`, `/reliability`, `/insights`, `/anomalies`, `/bottlenecks`, `/trends`, `/integrations`, `/simulator`, `/ai-analysis`, `/settings`, `*` → NotFound. Lazy-load pages via `React.lazy` (one seam for future code-splitting).
- State: no Redux; `AppContext` holds `{ teamId, setTeamId, timeRange, setTimeRange }`. Team list is static placeholder (`team-alpha`, `team-beta`) until Phase 21/22 provides org/team APIs.
- Styling: plain CSS (`src/styles.css`, CSS variables, no Tailwind dependency) to keep Phase 17 dependency-light; dark sidebar + light content matching CodeSense brand.
- Tooling: Vite 5 + React 18 + TypeScript strict. `vite.config.ts` with `/api` proxy to `http://localhost:8000` for dev. `tsconfig` strict + `noUnusedLocals`.
- No Recharts/Plotly in Phase 17 (Phase 18 adds charts). No auth (Phase 22). No real dashboard data (Phase 18).
- Prototype note: none — no prior UI prototype; decisions above are the full contract.

## Testing Decisions

- What makes a good test here: test external behavior at the highest seam — router renders every route, apiClient builds correct URLs/methods, layout exposes selectors — not CSS internals.
- Modules to test: `apiClient` URL/method construction (mocked fetch), router smoke (all 14 routes resolve without crash). Verified in this phase by `npm run build` (tsc + vite) + a Node smoke script asserting route table + apiClient surface. Full Vitest + Playwright deferred to Phase 23.
- Prior art: backend uses `pytest` + `httpx` integration tests (`tests/`); frontend mirrors that with build-gate + smoke until Phase 23 adds `*.test.tsx`.

## Out of Scope

Phase 18 dashboards (real charts, metric wiring, drill-down), Phase 19 LLM explainer UI beyond a static placeholder, Phase 20 privacy/offline badges beyond generic error states, Phase 21 provider integrations pages beyond static placeholder, Phase 22 auth/RBAC (UserMenu is static), Prometheus/Grafana embedding.

## Further Notes

- Backend CORS already `allow_origins=["*"]` (`backend/app/main.py:41`), so dev proxy is convenience, not requirement.
- Backend routers present: health, events, metrics, risk, anomalies, bottlenecks, insights, health-score, ml (`backend/app/main.py:53-61`).
- Keep weights/configurability (health-score weights) out of UI until Phase 18; Settings page is placeholder.
