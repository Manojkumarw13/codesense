# CodeSense Rebuild — Design (Dashboard + Landing)

Date: 2026-10-11. Scope approved: dashboard + landing. Stack approved: Vite + shadcn.
Supersedes direction of `docs/superpowers/plans/2026-10-07-codesense-frontend-rebuild.md` (dashboard-only) by adding public landing routes in the same Vite app.

## 1. Intent (agreed)

Rebuild deleted `frontend/` (removed in `31bdf89`) as a premium, classic, professional Vite + React + TS + shadcn/ui app: public landing (`/`, `/product`, `/docs`) plus authenticated-shape dashboard (`/app/*`, 14 pages + 3 signal-detail routes), wired to FastAPI `http://localhost:8000/api/v1` and simulator `http://localhost:8001`. Backend is untouched. PLAN.md React+TS mandate holds.

## 2. Architecture

Vite SPA. Single typed `apiClient` seam (`BASE_URL = VITE_API_BASE_URL ?? localhost:8000/api/v1`), separate `simulatorClient` (`SIM_BASE = VITE_SIMULATOR_URL ?? localhost:8001`). `{total,skip,limit,items}` envelopes unwrapped to arrays. UUID-gated filters (placeholder team names never sent). `AppContext` holds display-only `{teamId, timeRange}`. Lazy routes under public layout vs app shell layout. Recharts confined to lazy chart chunk. nginx `dist` + `dashboard` compose service.

## 3. Visual system

Restrained strategy: tinted neutrals + indigo accent ≤10% + severity hues. Tokens: `--bg #f6f9fc`, `--panel #ffffff`, `--ink #0d253d`, `--ink-2 #273951`, `--muted #5b6b83`, `--line #e3e8ee`, `--accent #533afd`, `--accent-deep #4434d4`, `--sidebar #1c1e54`. OKLCH equivalents in Tailwind theme. Inter (`ss01`, `tnum` on numerics), `balance` h1–h3, contrast ≥4.5:1. Bans: no cream/sand body, no side-stripe borders, no gradient text, no decorative glass, no hero-metric cliché, no identical card grids, no eyebrow-per-section (group label only), semantic z-index.

## 4. IA

Public layout: `/` (hero score composition, pipeline COLLECT→VISUALIZE, privacy boundary, dimensions, scenario strip, CTA), `/product` (flows + evidence chain), `/docs` (entry to `docs/`). App shell `/app`: groups Analyze (Overview, Health, Trends), Flows (Delivery, Development, CICD, Reliability), Signals (Insights, Anomalies, Bottlenecks + `/:id` details), System (Integrations, Simulator, AI Analysis, Settings). One `h1` per page, back-links on details.

## 5. States & constraints

Loading → Skeleton; empty → EmptyState ("run the simulator"); error/offline → ErrorState/EmptyState, never blank. AI unconfigured → calm fallback notice. `GET /metrics` (Prometheus text) never fetched. Team-level only: no identity rendered or sent to LLM; 422 privacy-block renders fallback. Reduced-motion collapses to instant. Gzip budgets: charts ≤130KB, entry ≤60KB. 375/768/1024/1440 tiers; drawer + scrim + Escape under 768px.

## 6. Self-review

No TBD. Consistent with PLAN.md §§1–11, Application Flow Score→Evidence chain, API endpoint truth (§1 of plan). Scope fits one plan: landing adds 3 routes + shared tokens, no second deployable. Ambiguity resolved: Next.js rejected (ops cost), plain-CSS restore rejected (debt), pricing page omitted (no MVP pricing).
