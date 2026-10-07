# Stripe Phase 9 — Final Testing & Audit Spec

## Problem Statement

Eight phases of change need one consolidated proof: nothing regressed, contrast holds on the new ink scale, forced-colors was dispositioned, and the full gate passes on the final tree.

## Solution

Run every gate in sequence (unit, budgets, full Playwright, contrast pairs, forced-colors render), record verdicts, and commit. No product changes unless a gate fails.

## User Stories

1. As a maintainer, I want one report proving the redesign, so that each phase's claim is backed by a final run.
2. As a low-vision user, I want contrast verified on the shipped palette, so that muted/small text is readable.
3. As a Windows-high-contrast user, I want a forced-colors verdict, so that the gap is explicit, not unknown.

## Implementation Decisions

- Contrast: in-page luminance math on shipped pairs (ink/panel, muted/panel, info-badge, ok-badge); bar is 4.5:1 for text.
- Forced-colors: render probe with `forcedColors: 'active'` asserting content present and interactive; verdict recorded even if imperfect (explicit follow-up, not silent).
- Sequence: pytest (ordering/ai/foundation) → budgets → Playwright full → probes → commit.

## Testing Decisions

- Highest seam: the gates themselves; this phase adds no new product code by default.
- Prior art: all phase probes and the 35-test harness.

## Out of Scope

New features, screenshot-diff infrastructure (deferred: needs a stable baseline environment first), fixing anything the audit finds beyond trivial — findings become follow-up phases.

## Further Notes

- Harness accommodations to date (favicon stub, expected-offline filters, retry:1, localhost API base) are documented here as methodology, not product behavior.
