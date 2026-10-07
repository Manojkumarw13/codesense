# Stripe Phase 2 — Component System Spec

## Problem Statement

Tokens are in place but components still speak the old language: rounded-rect buttons, neutral shadows, blue (non-indigo) charts, dead CSS from deleted components. The UI reads as "close, but generic".

## Solution

Restyle the shared component layer to Stripe prescriptions — pill buttons with press states, hairline inputs with indigo focus, soft-pill badges, hairline+Level-1 cards, indigo chart palette — and delete dead CSS. No JSX logic changes; one chart-constant change.

## User Stories

1. As a user, I want pill CTAs with clear pressed states, so that actions feel decisive and consistent.
2. As a user, I want inputs whose focus state is unmistakable, so that keyboard and pointer use stay oriented.
3. As a user, I want badges that read as quiet tags, not loud pills, so that severity scans without shouting.
4. As a user, I want cards with hairline edges and soft lift, so that surfaces feel premium on white.
5. As a developer, I want dead CSS removed, so that the stylesheet stays maintainable.

## Implementation Decisions

- `.btn`: pill radius, 8×16 padding, indigo fill; `:hover` deep, `:active` press bg + scale(0.97); new `.btn-secondary` (white, 1px indigo border, indigo text) and `.btn-sm` (14px label); min-height 40px (AAA touch).
- `.selector select`: border `var(--line-input)`, radius sm(6px); `:focus-visible` border indigo (keep global outline).
- `.badge`: pill radius, micro-cap treatment (10px/400/0.1px uppercase stays 11.5px for legibility — Stripe micro-cap at small sizes harms scanning; documented deviation); info tone → subdued `#b9b9f9` bg + `#4434d4` text.
- `.card`: `1px solid var(--line)` + `var(--shadow-1)`; hover `var(--shadow-2)`; radius lg(12px).
- Charts (`ScoreCharts.tsx`): `ACCENT #533afd`; `DIM_COLORS` indigo-family + ruby `#ea2261` (file sanctions ruby as chart highlight).
- Sidebar active pill → indigo tint; nav hover unchanged.
- Delete dead rules: `.chart`, `.trend-line`, `.trend-dot`, `.dim-*` (components deleted in Recharts pass).
- Toasts/skeletons: unchanged (already Sonner/canvas-correct).

## Testing Decisions

- Highest seam: computed-style probe (btn radius, card border-color, first chart stroke) + full 35-test suite (behavioral no-regression).
- Prior art: Phase 1 token probe.

## Out of Scope

Top-bar/IA (Phase 3), page content (Phase 4), responsive additions (Phase 5), new motion (Phase 6), h1/a11y (Phase 7).

## Further Notes

- Severity hues stay (product scope); only badge *treatment* changes.
