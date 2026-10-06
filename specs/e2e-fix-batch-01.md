# E2E Fix Batch 01 Spec (FE-01 + INT-01)

## Problem Statement

Playwright E2E (35/35 passing after harness accommodations) surfaced two real gaps: browsers intermittently log a `favicon.ico` 404 on every page, and list APIs return nondeterministic order when rows share a timestamp — the Overview once rendered 80.5 as "latest" instead of 68.9, and different `limit` values returned different first rows.

## Solution

Ship a favicon so no page ever 404s, and add an `id` tiebreaker to every list-endpoint ordering so equal timestamps always resolve to the same stable order. Both fixes are tiny, dependency-free, and covered by regression tests.

## User Stories

1. As a user, I want zero console errors on page load, so that real problems are never hidden in 404 noise.
2. As an engineering leader, I want the "latest" health score to actually be the latest, so that Overview/Health/Trends never show a stale score first.
3. As a developer, I want paginated list APIs to be stable, so that `limit=30` and `limit=100` agree on the first row.
4. As a developer, I want a regression test proving tied timestamps resolve deterministically, so that this cannot silently regress.
5. As an operator, I want no migration, no new env vars, and no new dependencies from these fixes.

## Implementation Decisions

- FE-01: new `frontend/public/favicon.svg` (CodeSense mark, currentColor-blue rounded square with white pulse line) + `<link rel="icon" type="image/svg+xml" href="/favicon.svg">` in `index.html`. No binary `.ico`: modern browsers use the SVG link and skip the legacy request (validated empirically with an unstubbed probe).
- INT-01: append `id.desc()` as secondary sort to all 7 list orderings (health-score by `calculated_at`, insights by `created_at`, anomalies/bottlenecks by `detected_at`, ml models/features by `created_at`, events by `created_at`). Primary sort untouched — no behavior change except tie stability.
- Regression test: new `tests/unit/test_ordering_stability.py` hits `GET /health-score` over a real DB (same live-Postgres precondition as `test_database.py`) with two tied-`calculated_at` marker rows under a scratch org/team, asserts both `limit=1` and `limit=100` return the same first row, cleans up in `finally`.
- No schema change, no migration, no API shape change (same envelopes, same fields).

## Testing Decisions

- What makes a good test: external behavior at the highest seam — HTTP response order for tied rows, HTTP 200 for the icon, icon link present in served HTML — not ORM internals.
- Modules to test: `GET /health-score` ordering (new test); favicon via `curl` + unstubbed Playwright probe + `vite build` emitting the asset; full Playwright suite re-run as the gate (35/35 expected).
- Prior art: `tests/unit/test_database.py` (live-DB pattern), `tests/unit/test_ai_explainer.py` (TestClient seam), `/tmp` Playwright harness with route/console collectors.

## Out of Scope

Changing primary sort keys (e.g. health-score to `period_end`), backfilling a binary `.ico`, DB-level index changes, touching dashboard code (it already renders whatever is first — now correctly the latest).

## Further Notes

- The E2E seed that exposed INT-01 used one transaction (identical `server_default=now()` stamps); production ties are rarer but possible, hence the fix.
- Playwright harness keeps its favicon stub (harness-only, product untouched); FE-01 is proven by the unstubbed probe instead.
