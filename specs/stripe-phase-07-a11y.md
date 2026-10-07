# Stripe Phase 7 — Accessibility Spec

## Problem Statement

No page has an `h1`, there is no skip link, the drawer cannot be closed via keyboard, `--faint` may fail contrast on small text, and charts expose no text alternative — each a concrete WCAG gap in an otherwise polished UI.

## Solution

Promote page titles to `h1` (same visual style), add a skip-to-content link, close the drawer on Escape, verify `aria-current` on the active nav link, audit `--faint` usage for contrast, and label chart regions.

## User Stories

1. As a screen-reader user, I want one `h1` per page, so that page identity is announced.
2. As a keyboard user, I want a skip link, so that I bypass 14 nav links on every page.
3. As a keyboard user, I want Escape to close the drawer, so that I am never trapped.
4. As a low-vision user, I want all small text at 4.5:1+, so that muted content stays readable.
5. As a screen-reader user, I want chart regions named, so that I know what each graphic shows.

## Implementation Decisions

- Bulk rename page-title `<h2>` → `<h1>` across `src/pages` (titles only; card titles stay `h3`); stylesheet rule moves `h2` → `h1` with identical values. Harness selectors update `main h2` → `main h1`.
- Skip link in `Layout` (`<a className="skip-link" href="#main-content">`) + `id="main-content"` on `<main>`; CSS hides until `:focus-visible`.
- Drawer: `Escape` key listener in `Layout` (closes only when open).
- `aria-current`: NavLink renders it natively — verified by probe, no code change if present.
- `--faint`: grep usages; any small light-bg text moves to `--muted`; dark-bg decorative uses stay.
- Charts: `role="img"` + `aria-label` on the three Recharts wrappers in `ScoreCharts.tsx`.

## Testing Decisions

- Highest seam: probe per route (exactly one `h1`, skip link jumps focus to main, active link has `aria-current="page"`, Escape closes drawer at 375px, chart regions named); full suite green after selector updates.
- Prior art: viewport/a11y probes.

## Out of Scope

Focus trapping in the drawer, live-region announcements for async data, forced-colors theme pass (deferred to Phase 9 audit — verdict there).

## Further Notes

- No visual change by design: `h1` inherits the exact former `h2` metrics.
