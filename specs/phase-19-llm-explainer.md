# Phase 19 — LLM Explainer Spec

## Problem Statement

Deterministic analytics (scores, anomalies, bottlenecks, insights) exist but speak in numbers. Users asking "why did the score drop?" get tables and evidence JSON, not a readable explanation. There is no AI layer, and — critically — no privacy boundary yet to make a future AI layer safe.

## Solution

Add an optional, synchronous LLM explainer behind a strict privacy gateway: the backend builds team-aggregate context, the gateway strips/blocks any developer identity, an OpenRouter-compatible model generates an explanation, and any AI failure falls back to the deterministic structured explanation. Core analytics never depend on AI. DoD: AI explains team-level analytics without ever receiving developer identity.

## User Stories

1. As an engineering leader, I want a plain-language explanation of a score change, so that I can report it without reading raw tables.
2. As an engineering leader, I want anomaly explanations, so that I know what changed and why it is unusual.
3. As an engineering leader, I want bottleneck explanations, so that I know why a workflow is stuck.
4. As an engineering leader, I want trend summaries, so that I can brief stakeholders.
5. As an engineering leader, I want investigation suggestions, so that my team knows what to check next.
6. As a privacy reviewer, I want any payload containing developer identity to be hard-blocked, so that a cloud LLM can never receive it.
7. As a privacy reviewer, I want raw event payloads and individual-level metrics excluded by construction, so that safety does not rely on caller discipline.
8. As a user, I want a useful explanation even when the LLM is down/offline/misconfigured, so that AI is leaf functionality with graceful fallback.
9. As a user, I want to know whether AI is configured or in fallback mode, so that expectations are honest.
10. As a developer, I want one HTTP seam (`POST /api/v1/ai/explain`), so that the UI and tests never touch LLM internals.
11. As an operator, I want no new required env vars and no DB migration, so that deployment is unchanged (AI activates when `OPENROUTER_API_KEY` is set).

## Implementation Decisions

- Modules to build: `privacy/gateway.py` (PrivacyGateway: allowlist-based context builder + denylist PII scan with hard block), `ai/client.py` (OpenRouter-compatible chat-completions POST via `requests`, timeout, `LLM_MODEL` default from settings), `ai/explainer.py` (per-use-case aggregate context + deterministic fallback texts), `api/endpoints/ai.py` (`POST /ai/explain`, `GET /ai/status`).
- Interfaces: `POST /ai/explain {use_case, team_id?, limit?}` → `{use_case, explanation, source, model?, sanitized_context}` where `source` is `CLOUD_AI` or `FALLBACK_RULES`. `GET /ai/status` → `{configured, model, mode}`. Use cases in order: `score_explanation → anomaly_explanation → bottleneck_explanation → trend_summary → investigation_suggestions`.
- Privacy contract (non-negotiable): only team-aggregate inputs (health scores incl. `component_metrics`, insight/anomaly/bottleneck rows minus raw payloads); denylist scan (email regex, `name/username/email/user_id/developer/actor/assignee/author/committer` keys, UUID-ish identity values in suspicious keys) raises `PrivacyBlockedError` → HTTP 422 `REQUEST BLOCKED`; raw `payload`/`raw_payload` keys always dropped; `actor_ref` never read.
- Failure contract: LLM timeout/error/misconfiguration → deterministic fallback built from the same aggregates (never an exception to the caller, except privacy blocks and bad use cases).
- No DB writes, no migration, no new required settings; `requests` already a dependency; no new frontend deps.
- Frontend: wire `AIAnalysis` page (use-case selector, Explain button, explanation card with `CLOUD_AI`/`FALLBACK_RULES` badge, sanitized-context evidence view, `GET /ai/status` banner); extend `apiClient` with `explain` + `getAiStatus`.

## Testing Decisions

- What makes a good test: external behavior at the highest seam — gateway blocks identity payloads; explainer falls back with no key; mocked LLM returns its text verbatim; endpoint returns 200/422 shapes — never real network.
- Modules to test: `PrivacyGateway` (block cases: email string, username key, actor_ref, raw payload strip), `explainer` fallback per use case, endpoint via `TestClient` with monkeypatched LLM call. Prior art: `tests/unit/test_insights.py`-style plain asserts, FastAPI `TestClient` as in `test_backend_foundation.py`.
- Frontend verified by `tsc` + `vite build` + smoke asserting the page wiring (existing Phase 17/18 pattern); full Vitest/Playwright deferred to Phase 23.

## Out of Scope

Async/background explanation jobs (sync MVP only), local-LLM provider switching UI, persisting explanations to `ai_insight_requests` (stateless this phase), auth-gating the endpoint (Phase 22), streaming responses, prompt-tuning dashboards.

## Further Notes

- `settings.OPENROUTER_API_KEY`/`LLM_MODEL`/`AI_GATEWAY_URL` already exist; `AIInsightRequest.sanitized_context` column exists but is unused this phase.
- The gateway applies to any future caller, not just this endpoint — it is the single choke point before LLM-bound data.
