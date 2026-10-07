# Stripe Phase 1 — Design Tokens Spec

## Problem Statement

The visual system lives in a single `styles.css` with ad-hoc values (generic blue `#2563eb`, near-black ink, single radius). There is no token layer, so the Stripe direction (navy ink, indigo hierarchy, hairlines, radius/spacing scales, tabular numerics) cannot be applied consistently or evolved safely.

## Solution

Extract a Stripe-mapped token layer (`styles/tokens.css`) keeping existing variable names so every component keeps working, load Inter (300–600, `display=swap`, system fallback for offline), and wire base typography (`ss01` globally, `tnum` utility for numerics). Components restyle in Phase 2; this phase changes raw values only where the variable already flows.

## User Stories

1. As a developer, I want one token file with Stripe values, so that Phase 2 component work references tokens, not hex codes.
2. As a user, I want Inter rendering with tight, premium type rhythm, so that the app reads as designed even before components change.
3. As a user, I want tabular numerals on scores and tables, so that numbers align and compare cleanly.
4. As an operator, I want the app to work offline without the webfont, so that Phase 20's offline guarantee holds (system-stack fallback).
5. As a developer, I want zero renamed variables, so that no JSX changes are needed in this phase.

## Implementation Decisions

- New module `frontend/src/styles/tokens.css` holding the full `:root` token set; `styles.css` keeps a leading `@import './styles/tokens.css'` — wait, Vite resolves relative to the CSS file, so the import lives at the top of `styles.css` as `@import './styles/tokens.css'` only if tokens move to a subfolder; decision: `src/styles/tokens.css`, imported first line of `src/styles.css`.
- Token mapping (Stripe → CodeSense names): `--bg #f6f9fc`, `--panel #ffffff`, `--ink #0d253d`, `--ink-2 #273951`, `--muted #64748d`, `--line #e3e8ee`, `--line-input #a8c3de`, `--accent #533afd`, `--accent-deep #4434d4`, `--accent-press #2e2b8c`, `--accent-soft #665efd`, `--accent-tint` → subdued `#b9b9f9` (bg) with `--accent-ink #4434d4` text pairing documented; severity tokens unchanged (product-UI scope, Phase 2 re-tint); radius scale xs/sm/md/lg/xl/pill added; spacing scale xxs–huge added; elevation L1/L2 blue-tinted shadows added as `--shadow-1/2`.
- Typography: Inter via Google Fonts `<link>` (weights 300;400;500;600;700, `display=swap`); body stack `Inter, ui-sans-serif, system-ui…`; `font-feature-settings: "ss01"` on body; `.tnum` utility (`font-feature-settings: "tnum"`, tracking -0.02em) applied to score-hero, table numerics, dim values (class additions only, no restyle).
- `h2` tightened to Stripe rhythm (20px/600/-0.02em at app scale — display-xl proportions, not marketing 48px).
- No JSX logic changes; no new dependencies; no API changes.

## Testing Decisions

- What makes a good test: external behavior at the highest seam — computed styles resolve to token values; every route still renders and behaves identically.
- Modules to test: token resolution via Playwright computed-style probe (`--accent` → `#533afd`, body font stack contains Inter when online, falls back offline); full 35-test suite as the no-regression gate.
- Prior art: Phase-fix computed-style probe pattern (reduced-motion), `/tmp` Playwright harness.

## Out of Scope

Component restyling (Phase 2: pills, inputs, badges, cards), dark-mode surfaces, font self-hosting (only if offline audit demands it in Phase 8), touching JSX beyond `tnum` class additions.

## Further Notes

- The accent shift (`#2563eb` → `#533afd`) flows automatically into focus rings, chart strokes, links, and badges via existing variables — intended, verified by screenshot-diff in Phase 9.
- Recharts hardcodes its own blue `#2563eb` in `ScoreCharts.tsx` — intentionally left for Phase 2's chart-palette pass (single coherent change, not drift).
