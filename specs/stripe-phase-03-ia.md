# Stripe Phase 3 — Information Architecture Spec

## Problem Statement

Fourteen flat routes with no orientation cues: a user landing on a deep link cannot tell which section family they are in, inline links use browser-default blue/purple (visual slop, off-palette), and there is no enforced CTA hierarchy.

## Solution

Derive a section eyebrow from the route (Analyze/Flows/Signals/System — same grouping as the sidebar), style all inline links as Stripe `link-on-light` (indigo, no underline), and audit that no band carries two competing filled primaries.

## User Stories

1. As a user, I want a section eyebrow above every page, so that deep links orient me instantly.
2. As a user, I want consistent indigo links, so that affordances scan uniformly.
3. As a user, I want one clear primary action per view, so that I never wonder what to click.

## Implementation Decisions

- `Layout` maps `pathname` → group label via the same order as `NAV_GROUPS` (single source duplicated minimally; no router restructure).
- Eyebrow: `.eyebrow` micro-cap style (10px/400/0.1px uppercase, muted) rendered above `Outlet`; pure function of route, no state.
- Global `a` rule: indigo, no underline; underline on hover only (keeps dense tables scannable).
- CTA audit outcome: AI Analysis keeps its single `.btn`; Overview uses text links only; no page has two filled primaries — no changes needed beyond the audit.

## Testing Decisions

- Highest seam: rendered DOM — probe asserts eyebrow text on 4 representative routes + computed link color; full suite (eyebrow must not disturb `main h2` selectors).
- Prior art: Phase 1/2 probes.

## Out of Scope

Route restructuring, breadcrumbs with history, header redesign (covered sufficiently by selectors + menu), page content (Phase 4).

## Further Notes

- Eyebrow duplicates sidebar grouping by value, not by import, to avoid coupling Layout to Sidebar internals.
