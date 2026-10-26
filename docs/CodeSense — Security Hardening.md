# CodeSense — Security Hardening

**Document Status:** Living Document  
**Version:** 1.0  
**Project:** CodeSense  
**Purpose:** Security controls, secrets handling, and verification for CodeSense.

---

## 1. Secrets (no hard-coded defaults in production)

`backend/app/core/settings.py` (`Settings`) rejects insecure `SECRET_KEY` defaults in `APP_ENV=production`:

```text
SECRET_KEY must be set via environment variable in production; insecure defaults are prohibited
```

Blocked defaults: `changeme`, `supersecretkeyreplaceinproduction`, `dev-only-insecure-change-me`. Development/tests use a labeled dev placeholder (`dev-only-insecure-change-me`) so auth keeps working without an env var. Never commit a real `SECRET_KEY`; use `.env` (gitignored) or environment variables.

AI credentials (`OPENROUTER_API_KEY`) are optional and must also come from the environment.

---

## 2. Rate limiting (all endpoints)

`RateLimitMiddleware` (`backend/app/core/middleware.py`) applies a token bucket to every request:

- 60 requests per 60-second window per client IP
- Redis-backed (atomic Lua script) when Redis is available; in-memory fallback otherwise
- Exceeding the limit returns `429` with `Retry-After: 1`
- Disabled under `pytest` so test bursts are not throttled

---

## 3. Security headers (every response)

`SecurityHeadersMiddleware` (`backend/app/core/middleware.py`) appends:

| Header | Value |
|---|---|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `Content-Security-Policy` | `default-src 'self'; base-uri 'self';` |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` |

`RequestIDMiddleware` adds `X-Request-ID` for request tracing.

---

## 4. Authentication

- JWT access tokens (`HS256`), 15-minute expiry (`ACCESS_TOKEN_EXPIRE_MINUTES`)
- Refresh tokens, 7-day expiry (`REFRESH_TOKEN_EXPIRE_DAYS`)
- Password hashing with bcrypt (`BCRYPT_ROUNDS=12`)
- Auth router mounted at `/api/v1/auth` (`backend/app/auth/router.py`)
- Protected routes use dependency injection (`backend/app/api/auth_deps.py`)

---

## 5. Privacy / AI data boundary

- Developer identity stripped before any LLM call (AI data boundary)
- `MIN_TEAM_SIZE=5`: detections below team-size threshold are masked
- `PRIVACY_PSEUDONYM_SALT` stabilizes actor pseudonyms across restarts (set in production)
- `EXPOSE_RAW_PAYLOADS=false`: raw payloads not exposed by default
- Core analytics work offline; LLM optional

---

## 6. Network

- CORS configured in `backend/app/main.py` (restrict `allow_origins` in production)
- nginx terminates on port 80 and proxies `/api/v1` to the backend; `/health` is a local self-check
- Compose services communicate over the `home-server-backend` network (external)

---

## 7. Verification

- `tests/integration/test_security_scan.py::test_no_hardcoded_secret_defaults` — asserts `SECRET_KEY` is not an insecure default
- Response headers include `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, etc.
- `GET /api/v1/health` returns 200 without leaking internals on DB failure (degrades to `DatabaseError`)
