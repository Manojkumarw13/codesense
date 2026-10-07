# Stripe Phase 4 — Pages Spec

## Problem Statement

Signal lists are dead ends (no drill-down), the Overview hero is uncomposed, and the Simulator page describes controls it cannot touch — even though a status/control API exists on `:8001`.

## Solution

Add detail routes for the three signal types (insight/anomaly/bottleneck: title, badges, evidence, related metrics, back link), compose the Overview hero (score + period + delta + sparkline in one card), and wire the Simulator page to the real simulator API with graceful offline handling.

## User Stories

1. As a user, I want to open a signal for full evidence, so that lists stay scannable and depth is one click away.
2. As a user, I want detail pages to show related metrics, so that Score → Dimension → Metric → Evidence completes.
3. As a user, I want simulator status and start/stop/scenario controls, so that demo data generation is operable from the UI.
4. As a user, I want a clear offline state when the simulator is down, so that I know how to fix it.

## Implementation Decisions

- New pages `InsightDetail`, `AnomalyDetail`, `BottleneckDetail` at `/insights/:id`, `/anomalies/:id`, `/bottlenecks/:id` using existing `apiClient` detail getters; list rows gain `Open →` links (counts unchanged).
- Detail layout: title, severity/category badges, meta table (detected/created, confidence, generated-by/status), `Evidence` block, related-metrics block from `source_metrics`/observed-baseline; back link to parent list.
- Simulator: `apiClient.getSimulatorStatus/start/stop/setScenario` against `VITE_SIMULATOR_URL ?? http://localhost:8001` (separate base — never the main `BASE_URL`); status card (running/paused, scenario, entity counts), start/stop buttons (`.btn`/`.btn-secondary`), scenario select; unreachable → `EmptyState` offline message. Toasts on actions.
- Overview hero: period range caption under the score; no structural change.

## Testing Decisions

- Highest seam: new routes render seeded detail (title + evidence), simulator card shows offline state without `:8001`, lists keep counts; full suite green.
- Prior art: existing detail getters already covered by backend 404 tests; Playwright route pattern.

## Out of Scope

Simulator tick/config controls, pause/resume buttons (status-scoped MVP), editing weights (backend read-only), new backend endpoints.

## Further Notes

- Detail routes reuse `Card`/`Badge`/`Evidence` — no new visual language.
