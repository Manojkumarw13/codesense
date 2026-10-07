# Stripe Phase 5 — Responsive Spec

## Problem Statement

One 860px breakpoint, tables that overflow small screens instead of scrolling, ~36px touch targets, and a drawer with no scrim (no tap-outside-to-close) — below the Stripe bar of 1024/768 breakpoints, 44px mobile targets, and single-panel simplification.

## Solution

Add the 1024px tier, move the drawer tier to 768px with a tap-outside scrim, wrap all data tables in horizontal scroll containers, and raise mobile touch targets to 44px.

## User Stories

1. As a tablet user, I want comfortable density at 1024px, so that dashboards don't jump straight from desktop to phone layout.
2. As a phone user, I want tables to scroll horizontally in place, so that no content is cut off or breaks layout.
3. As a phone user, I want 44px targets, so that taps land reliably.
4. As a phone user, I want tapping outside the drawer to close it, so that navigation never traps me.

## Implementation Decisions

- Breakpoints: `@media (max-width: 1024px)` (content padding 20px, grid min 240px); drawer tier moves 860px → 768px (class/behavior unchanged, only the query).
- `.table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }` wrappers added in Health, Anomalies, AnomalyDetail, Settings tables (only files rendering `.table`).
- 768px tier: `.nav-link` padding grows to 12px (≈48px rows), selects/buttons min-height 44px, filters stack full-width.
- Scrim: Layout renders `.scrim` button (aria-label Close navigation) when drawer open on mobile; CSS shows it only under 768px; click calls `onClose`.
- No desktop visual change; no new dependencies.

## Testing Decisions

- Highest seam: viewport probes — 375px (table scrolls: scrollWidth > clientWidth on wrap, drawer opens/closes via scrim), 1024px (no horizontal page overflow), 1440px (unchanged); full suite at default viewport.
- Prior art: computed-style/viewport probe pattern.

## Out of Scope

Chart simplification to single-panel (Recharts ResponsiveContainer already reflows; dedicated mobile chart variants deferred), landscape-specific rules, PWA work.

## Further Notes

- Drawer `transform` transition and reduced-motion handling already exist; scrim fades with the same token timing.
