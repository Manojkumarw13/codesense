# Stripe Phase 8 — Performance Spec

## Problem Statement

No enforced budgets: the Recharts chunk (~120KB gzip) could grow silently, font loading has no offline proof, and tree-shaking was never verified — performance is currently true by accident, not by contract.

## Solution

Add an enforceable gzip-budget script (`npm run budgets`), prove offline font fallback by blocking font hosts, and verify Recharts is only bundled via named imports in the chart chunk.

## User Stories

1. As a developer, I want `npm run budgets` to fail on overweight chunks, so that regressions are caught at build time.
2. As a user, I want readable fallback type when fonts are blocked, so that offline/slow networks never break layout.
3. As a developer, I want proof Recharts tree-shakes, so that non-chart routes stay lean.

## Implementation Decisions

- `frontend/scripts/check-budgets.mjs`: gzips `dist/assets/*.js`, asserts `ScoreCharts-* ≤ 130KB` and `index-* ≤ 60KB`; non-zero exit with a table on breach. Wired as `"budgets"` script (runs after build; CI can chain it later).
- Fonts: keep Google Fonts (`display=swap` + preconnect already present); offline proof via aborted-host probe asserting render + zero console errors.
- Treeshake: grep proves only `ScoreCharts.tsx` imports `recharts`; bundle listing shows recharts confined to its lazy chunk.

## Testing Decisions

- Highest seam: script exit code on current `dist/` (pass), probe with `fonts.g*` aborted (render + clean console), chunk listing.
- Prior art: build-gate pattern, interception probes.

## Out of Scope

Self-hosting fonts (unnecessary while fallback is proven), image optimization (no raster assets), service workers.

## Further Notes

- Budgets ratchet only downward; raising a budget requires a spec note.
