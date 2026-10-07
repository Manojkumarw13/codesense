# Stripe Phase 6 — Motion Spec

## Problem Statement

Toasts vanish instantly on dismiss/timeout — the exit has no subtlety, so stacked toasts jump. Everything else in the motion inventory (page enter, hover/press, drawer, charts, shimmer, spinner) already passed review; this closes the one gap.

## Solution

Two-phase toast unmount: dismissed toasts play a 150ms exit (opacity + 12px slide, no blur — subtler than the enter) before removal. Reduced-motion keeps instant removal.

## User Stories

1. As a user, I want toasts to leave gracefully, so that stacked notifications don't jump.

## Implementation Decisions

- `ToastProvider` gains an `exiting` id set: `dismiss()` marks exiting, removal follows after 150ms; auto-dismiss path reuses `dismiss()`.
- CSS `.toast-exiting` (opacity 0, translateY(6px), 150ms ease-out); global reduced-motion rule already collapses it to instant.
- No other motion added: disclosures stay instant (functional), charts keep 400ms draws, route enter stays 140ms opacity-only.

## Testing Decisions

- Highest seam: probe asserts a toast gains `.toast-exiting` on dismiss and is removed ~150ms later; reduced-motion probe from the rebuild still passes; full suite green.
- Prior art: toast/chrome probes.

## Out of Scope

New animations anywhere else, exit animations on cards/pages, spring physics.

## Further Notes

- Exit deliberately drops the blur (Jakub: exits subtler than enters).
