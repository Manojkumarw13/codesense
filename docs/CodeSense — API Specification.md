# CodeSense — API Specification

**Document Status:** Draft / Editable  
**Version:** 1.0  
**Project:** CodeSense  
**API Style:** REST  
**Base Path:** `/api/v1`  
**Backend:** FastAPI  
**Authentication:** Token-based authentication  
**Data Format:** JSON  
**Primary Database:** PostgreSQL

---

# 1. Purpose

This document defines the API contract for CodeSense.

The API provides controlled access to:

- Authentication
- Users and roles
- Organizations
- Teams
- Projects
- Repositories
- Provider integrations
- Event ingestion
- Analytics
- Engineering Health Score
- Engineering trends
- AI-generated insights
- Configuration
- Audit logs
- System health

The API must enforce the architectural constraints defined in:

- `PRD.md`
- `SYSTEM_ARCHITECTURE.md`
- `DATABASE_SCHEMA.md`
- `DATA_FLOW.md`
- `AI_DATA_BOUNDARY.md`

---

# 2. API Architecture

```text
Frontend
    │
    ▼
API Gateway
    │
    ├── Authentication
    ├── Authorization
    ├── Validation
    ├── Rate Limiting
    └── Audit Logging
    │
    ▼
Application Services
    │
    ├── Identity Service
    ├── Project Service
    ├── Integration Service
    ├── Event Service
    ├── Analytics Service
    ├── Health Service
    ├── AI Service
    └── Configuration Service
    │
    ▼
PostgreSQL / Workers / AI Gateway
```

---

# 3. Base URL

Development:

```text
http://localhost:8000/api/v1
```

Production:

```text
https://<codesense-domain>/api/v1
```

The production domain must be configured through environment variables.

---

# 4. API Versioning

All public APIs must include a version:

```text
/api/v1/...
```

Breaking changes must create a new API version.

Example:

```text
/api/v1/projects
/api/v2/projects
```

Do not silently change the meaning of an existing endpoint.

---

# 5. Authentication

CodeSense APIs require authentication unless explicitly marked as public.

Example:

```http
Authorization: Bearer <access_token>
```

Authentication endpoints:

```text
POST /api/v1/auth/login
POST /api/v1/auth/logout
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
```

---

# 6. Authentication API

## 6.1 Login

```http
POST /api/v1/auth/login
```

### Request

```json
{
  "email": "user@example.com",
  "password": "password"
}
```

### Response

```json
{
  "access_token": "<token>",
  "refresh_token": "<refresh-token>",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Errors

```text
401 INVALID_CREDENTIALS
403 ACCOUNT_DISABLED
429 RATE_LIMITED
```

---

# 7. Logout

```http
POST /api/v1/auth/logout
```

Response:

```json
{
  "message": "Successfully logged out"
}
```

---

# 8. Refresh Token

```http
POST /api/v1/auth/refresh
```

### Request

```json
{
  "refresh_token": "<refresh-token>"
}
```

### Response

```json
{
  "access_token": "<new-token>",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

# 9. Current User

```http
GET /api/v1/auth/me
```

### Response

```json
{
  "id": "uuid",
  "organization_id": "uuid",
  "email": "user@example.com",
  "display_name": "User",
  "roles": [
    "ENGINEERING_MANAGER"
  ]
}
```

---

# 10. Organizations API

## Get Organization

```http
GET /api/v1/organizations/{organization_id}
```

## Update Organization

```http
PATCH /api/v1/organizations/{organization_id}
```

### Request

```json
{
  "name": "Example Engineering"
}
```

---

# 11. Users API

## List Users

```http
GET /api/v1/users
```

Query parameters:

```text
page
page_size
status
role
team_id
search
```

Example:

```text
GET /api/v1/users?page=1&page_size=20&status=active
```

---

## Get User

```http
GET /api/v1/users/{user_id}
```

---

## Create User

```http
POST /api/v1/users
```

### Request

```json
{
  "email": "developer@example.com",
  "display_name": "Developer",
  "role_ids": [
    "uuid"
  ]
}
```

---

## Update User

```http
PATCH /api/v1/users/{user_id}
```

---

## Disable User

```http
POST /api/v1/users/{user_id}/disable
```

---

# 12. Roles API

## List Roles

```http
GET /api/v1/roles
```

## Get Role

```http
GET /api/v1/roles/{role_id}
```

## Assign Role

```http
POST /api/v1/users/{user_id}/roles
```

### Request

```json
{
  "role_id": "uuid"
}
```

## Remove Role

```http
DELETE /api/v1/users/{user_id}/roles/{role_id}
```

---

# 13. Teams API

## List Teams

```http
GET /api/v1/teams
```

Query:

```text
page
page_size
status
search
```

## Get Team

```http
GET /api/v1/teams/{team_id}
```

## Create Team

```http
POST /api/v1/teams
```

### Request

```json
{
  "name": "Platform Engineering",
  "description": "Platform team"
}
```

## Update Team

```http
PATCH /api/v1/teams/{team_id}
```

## Delete/Archive Team

```http
DELETE /api/v1/teams/{team_id}
```

---

# 14. Team Members API

## List Members

```http
GET /api/v1/teams/{team_id}/members
```

## Add Member

```http
POST /api/v1/teams/{team_id}/members
```

### Request

```json
{
  "user_id": "uuid",
  "role": "MEMBER"
}
```

## Remove Member

```http
DELETE /api/v1/teams/{team_id}/members/{user_id}
```

---

# 15. Projects API

## List Projects

```http
GET /api/v1/projects
```

Query parameters:

```text
page
page_size
status
team_id
search
```

---

## Get Project

```http
GET /api/v1/projects/{project_id}
```

---

## Create Project

```http
POST /api/v1/projects
```

### Request

```json
{
  "name": "CodeSense",
  "key": "CODESENSE",
  "description": "Engineering intelligence platform"
}
```

---

## Update Project

```http
PATCH /api/v1/projects/{project_id}
```

---

## Archive Project

```http
POST /api/v1/projects/{project_id}/archive
```

---

# 16. Project Members API

## List Members

```http
GET /api/v1/projects/{project_id}/members
```

## Add Member

```http
POST /api/v1/projects/{project_id}/members
```

### Request

```json
{
  "user_id": "uuid",
  "access_level": "CONTRIBUTOR"
}
```

## Remove Member

```http
DELETE /api/v1/projects/{project_id}/members/{user_id}
```

---

# 17. Repository API

## List Repositories

```http
GET /api/v1/projects/{project_id}/repositories
```

## Get Repository

```http
GET /api/v1/repositories/{repository_id}
```

## Synchronize Repository

```http
POST /api/v1/repositories/{repository_id}/sync
```

### Response

```json
{
  "job_id": "uuid",
  "status": "QUEUED"
}
```

---

# 18. Provider API

## List Supported Providers

```http
GET /api/v1/providers
```

Example response:

```json
{
  "providers": [
    {
      "id": "uuid",
      "name": "GitHub",
      "provider_type": "SOURCE_CONTROL",
      "status": "AVAILABLE"
    }
  ]
}
```

---

# 19. Provider Connections API

## List Connections

```http
GET /api/v1/provider-connections
```

## Get Connection

```http
GET /api/v1/provider-connections/{connection_id}
```

## Create Connection

```http
POST /api/v1/provider-connections
```

### Request

```json
{
  "provider_id": "uuid",
  "name": "Engineering GitHub",
  "base_url": "https://api.example.com",
  "credential_reference": "secret-reference"
}
```

Credentials must not be returned in API responses.

---

# 20. Validate Provider Connection

```http
POST /api/v1/provider-connections/{connection_id}/validate
```

Response:

```json
{
  "status": "VALID",
  "checked_at": "2026-08-20T12:00:00Z"
}
```

---

# 21. Provider Synchronization

```http
POST /api/v1/provider-connections/{connection_id}/sync
```

Response:

```json
{
  "job_id": "uuid",
  "status": "QUEUED"
}
```

---

# 22. Webhook API

Provider webhook endpoint:

```http
POST /api/v1/webhooks/{provider}/{connection_id}
```

Example:

```text
POST /api/v1/webhooks/github/connection-uuid
```

The endpoint must:

1. Validate the webhook signature.
2. Identify the provider.
3. Identify the connection.
4. Preserve the original payload.
5. Store the raw event.
6. Return quickly.
7. Process the event asynchronously.

Response:

```json
{
  "received": true,
  "event_id": "uuid"
}
```

---

# 23. Raw Events API

Raw events are primarily an internal/system resource.

Normal users should not have unrestricted access.

## List Raw Events

```http
GET /api/v1/raw-events
```

Query:

```text
provider_connection_id
event_type
processing_status
from
to
page
page_size
```

---

## Get Raw Event

```http
GET /api/v1/raw-events/{event_id}
```

Access should be restricted to authorized administrative or diagnostic roles.

---

# 24. Canonical Events API

## List Canonical Events

```http
GET /api/v1/events
```

Query:

```text
project_id
repository_id
event_type
team_id
from
to
page
page_size
```

---

## Get Canonical Event

```http
GET /api/v1/events/{event_id}
```

Example:

```json
{
  "id": "uuid",
  "event_type": "PULL_REQUEST",
  "project_id": "uuid",
  "repository_id": "uuid",
  "occurred_at": "2026-08-20T10:30:00Z",
  "metadata": {}
}
```

---

# 25. Analytics API

Analytics are primarily calculated from canonical data.

## Dashboard Summary

```http
GET /api/v1/analytics/dashboard
```

Query:

```text
project_id
team_id
from
to
```

Example response:

```json
{
  "period": {
    "from": "2026-08-01",
    "to": "2026-08-20"
  },
  "metrics": {
    "deployment_frequency": 12,
    "change_lead_time": 3.2,
    "change_failure_rate": 0.08,
    "review_cycle_time": 5.4
  }
}
```

Units and metric definitions must be documented.

---

# 26. Metric Definitions API

## List Metrics

```http
GET /api/v1/metrics
```

## Get Metric Definition

```http
GET /api/v1/metrics/{metric_id}
```

Example:

```json
{
  "id": "uuid",
  "name": "deployment_frequency",
  "category": "DELIVERY",
  "aggregation_level": "TEAM"
}
```

---

# 27. Metric Values API

## Get Metric Values

```http
GET /api/v1/metrics/{metric_id}/values
```

Query:

```text
organization_id
project_id
team_id
from
to
aggregation_period
```

Response:

```json
{
  "metric": "deployment_frequency",
  "values": [
    {
      "period_start": "2026-08-01T00:00:00Z",
      "period_end": "2026-08-07T23:59:59Z",
      "value": 10
    }
  ]
}
```

---

# 28. Engineering Health API

## Current Engineering Health

```http
GET /api/v1/health/engineering
```

Query:

```text
project_id
team_id
```

Response:

```json
{
  "score": 82.4,
  "score_version": "1.0",
  "period": {
    "from": "2026-08-01",
    "to": "2026-08-20"
  },
  "components": {
    "delivery": 84,
    "quality": 80,
    "reliability": 83
  }
}
```

---

# 29. Engineering Health History

```http
GET /api/v1/health/engineering/history
```

Query:

```text
project_id
team_id
from
to
```

Response:

```json
{
  "history": [
    {
      "period": "2026-08-01",
      "score": 78.2
    },
    {
      "period": "2026-08-08",
      "score": 80.5
    },
    {
      "period": "2026-08-15",
      "score": 82.4
    }
  ]
}
```

---

# 30. Individual Productivity Restriction

The API must NOT expose endpoints such as:

```text
GET /developers/{id}/productivity
GET /users/{id}/productivity-score
POST /productivity-score
```

Individual productivity scoring is not a CodeSense feature.

Individual operational metrics may be exposed only where legitimate, documented, and protected by access controls.

---

# 31. Engineering Trends API

## List Trends

```http
GET /api/v1/analytics/trends
```

Query:

```text
project_id
team_id
metric_id
from
to
```

Response:

```json
{
  "trends": [
    {
      "metric": "review_cycle_time",
      "trend_type": "IMPROVING",
      "magnitude": 0.18,
      "confidence": 0.91
    }
  ]
}
```

---

# 32. Hybrid ML API

Endpoints for the Hybrid ML architecture (Global -> Org -> Team scope, no individual modeling).

## Get Predictions
```http
GET /api/v1/ml/predictions
```

## List Models
```http
GET /api/v1/ml/models
```

## Trigger Training
```http
POST /api/v1/ml/train
```

## Get Features
```http
GET /api/v1/ml/features
```

All predictions must return `confidence` and `evidence` fields.

---

# 33. AI Insights Architecture

AI requests must always pass through:

```text
Analytics
    ↓
Insight Preparation
    ↓
Privacy Sanitization
    ↓
AI Gateway
    ↓
LLM
```

The frontend must not directly communicate with the LLM provider.

---

# 33. AI Insight API

## Generate Insight

```http
POST /api/v1/insights/generate
```

### Request

```json
{
  "project_id": "uuid",
  "insight_type": "ENGINEERING_TREND",
  "metric_ids": [
    "uuid"
  ],
  "period": {
    "from": "2026-08-01",
    "to": "2026-08-20"
  }
}
```

The backend constructs the sanitized AI context.

The client must not provide arbitrary raw database data to the AI service.

---

# 34. AI Request Processing

Response (Synchronous Real-Time Generation):

```json
{
  "id": "uuid",
  "request_id": "uuid",
  "type": "ENGINEERING_TREND",
  "title": "Review cycle time increased",
  "content": "The review cycle time increased during the selected period.",
  "confidence": 0.88,
  "created_at": "2026-08-20T12:00:00Z"
}
```

Processing (Synchronous, blocking call):

```text
POST /insights/generate
          ↓
Create AI Request
          ↓
Prepare Analytics Context
          ↓
Remove Sensitive Identity (PII Stripped)
          ↓
AI Gateway (Synchronous)
          ↓
LLM
          ↓
Validate Response
          ↓
Store Insight & Return to Client
```

---

# 35. Get AI Insight

```http
GET /api/v1/insights/{insight_id}
```

Response:

```json
{
  "id": "uuid",
  "type": "ENGINEERING_TREND",
  "title": "Review cycle time increased",
  "content": "The review cycle time increased during the selected period.",
  "confidence": 0.88,
  "created_at": "2026-08-20T12:00:00Z"
}
```

---

# 36. List Insights

```http
GET /api/v1/insights
```

Query:

```text
project_id
team_id
insight_type
status
from
to
page
page_size
```

---

# 37. AI Privacy Rules

The following information must NEVER be sent to a cloud LLM:

```text
Developer names
Developer email addresses
Developer IDs
Authentication tokens
Provider credentials
API keys
Secrets
Raw provider payloads
Private credentials
Unfiltered personal information
```

The AI Gateway must sanitize the request before sending it externally.

---

# 38. Offline API Behavior

When CodeSense operates without Internet connectivity:

```text
Available:

GET /analytics/*
GET /health/*
GET /events/*
GET /projects/*
GET /repositories/*
```

subject to local data availability.

Cloud AI endpoints may return:

```http
503 SERVICE_UNAVAILABLE
```

with:

```json
{
  "error": {
    "code": "AI_UNAVAILABLE_OFFLINE",
    "message": "Cloud AI is unavailable while CodeSense is operating offline."
  }
}
```

Core analytics must continue working.

---

# 39. Configuration API

## Get Configuration

```http
GET /api/v1/configuration
```

## Update Configuration

```http
PATCH /api/v1/configuration
```

Example:

```json
{
  "analytics": {
    "default_period": "30d"
  },
  "ai": {
    "enabled": true
  }
}
```

Sensitive secrets must not be returned.

---

# 40. Audit API

## List Audit Logs

```http
GET /api/v1/audit-logs
```

Query:

```text
actor_user_id
action
resource_type
from
to
page
page_size
```

Access must be restricted.

---

# 41. Background Job API

## Get Job Status

```http
GET /api/v1/jobs/{job_id}
```

Response:

```json
{
  "id": "uuid",
  "type": "PROVIDER_SYNC",
  "status": "PROCESSING",
  "attempts": 1,
  "created_at": "2026-08-20T12:00:00Z"
}
```

---

# 42. Health Check API

## Basic Health

```http
GET /api/v1/health
```

Response:

```json
{
  "status": "healthy"
}
```

---

# 43. Detailed Health

```http
GET /api/v1/health/detailed
```

Example:

```json
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "workers": "healthy",
    "providers": "healthy",
    "ai_gateway": "available"
  }
}
```

AI gateway failure must not automatically mark the entire CodeSense platform as unhealthy.

---

# 44. API Response Format

Successful responses should use consistent structures.

Single resource:

```json
{
  "data": {
    "id": "uuid"
  }
}
```

Collection:

```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 100
  }
}
```

---

# 45. Error Response Format

All API errors should follow:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {}
  },
  "request_id": "uuid"
}
```

Example:

```json
{
  "error": {
    "code": "PROJECT_NOT_FOUND",
    "message": "The requested project does not exist.",
    "details": {}
  },
  "request_id": "uuid"
}
```

---

# 46. Standard HTTP Status Codes

```text
200 OK
201 CREATED
202 ACCEPTED
204 NO_CONTENT

400 BAD_REQUEST
401 UNAUTHORIZED
403 FORBIDDEN
404 NOT_FOUND
409 CONFLICT
422 UNPROCESSABLE_ENTITY
429 TOO_MANY_REQUESTS

500 INTERNAL_SERVER_ERROR
502 BAD_GATEWAY
503 SERVICE_UNAVAILABLE
```

---

# 47. Pagination

Collection endpoints should support:

```text
?page=1&page_size=20
```

Recommended maximum:

```text
page_size <= 100
```

Large datasets must not be returned in a single response.

---

# 48. Filtering

Use query parameters for filtering.

Example:

```text
GET /api/v1/events
    ?project_id=uuid
    &event_type=PULL_REQUEST
    &from=2026-08-01
    &to=2026-08-20
```

---

# 49. Sorting

Collection APIs should support:

```text
?sort=created_at
?sort=-created_at
```

Where supported.

The API must whitelist sortable fields.

---

# 50. Rate Limiting

Rate limits should be applied to:

- Authentication endpoints
- Provider APIs
- AI insight generation
- Expensive analytics
- Administrative operations

Example:

```text
Authentication:
10 requests/minute/IP

AI generation:
20 requests/minute/user

General API:
100 requests/minute/user
```

Exact production limits should be configurable.

---

# 51. Idempotency

Operations that may be retried must support idempotency where appropriate.

Example:

```http
Idempotency-Key: <unique-key>
```

Especially important for:

```text
Webhook ingestion
Provider synchronization
AI insight generation
Resource creation
```

---

# 52. Webhook Idempotency

Provider events must be deduplicated using:

```text
provider_connection_id
+
provider_event_id
```

The same provider event must not create duplicate canonical events.

---

# 53. Authorization Rules

Every protected endpoint must check:

```text
Authentication
      ↓
Organization membership
      ↓
Role permission
      ↓
Resource access
```

Example:

```text
User
 ↓
Organization A
 ↓
Project A
 ↓
Allowed

User
 ↓
Organization B
 ↓
Project A
 ↓
Forbidden
```

---

# 54. API Security Requirements

The API must implement:

- TLS in production
- Secure authentication
- RBAC
- Input validation
- Output validation
- Request size limits
- Rate limiting
- Secure headers
- CORS restrictions
- Audit logging
- Secret protection
- SQL injection protection
- Provider webhook signature validation

---

# 55. API-to-Database Rule

The frontend must never directly access PostgreSQL.

```text
Frontend
   X
   │
   ▼
PostgreSQL

Correct:

Frontend
   ↓
API
   ↓
Service Layer
   ↓
Repository Layer
   ↓
PostgreSQL
```

---

# 56. API-to-AI Rule

The frontend must never directly call the external LLM.

Incorrect:

```text
Frontend
    ↓
Cloud LLM
```

Correct:

```text
Frontend
    ↓
CodeSense API
    ↓
AI Service
    ↓
Privacy Filter
    ↓
AI Gateway
    ↓
Cloud / Local LLM
```

---

# 57. API-to-Provider Rule

Provider-specific logic must remain inside provider adapters.

```text
API
 ↓
Integration Service
 ↓
Provider Adapter
 ↓
External Provider
```

The API should not contain provider-specific parsing logic.

---

# 58. Core API Dependency Flow

```text
                    Frontend
                       │
                       ▼
                  API Gateway
                       │
          ┌────────────┼─────────────┐
          ▼            ▼             ▼
      Identity      Projects      Analytics
          │            │             │
          │            │             ▼
          │            │       Canonical Data
          │            │             │
          │            │             ▼
          │            │       Health Engine
          │            │             │
          │            │             ▼
          │            │        AI Gateway
          │            │
          ▼            ▼
      PostgreSQL ← Integration Service
                         │
                         ▼
                  Provider Adapters
```

---

# 59. API Testing Requirements

Every endpoint must have appropriate tests.

## Unit Tests

Test:

- Request validation
- Business logic
- Authorization
- Serialization

## Integration Tests

Test:

- API + PostgreSQL
- API + provider adapters
- API + workers
- API + AI gateway

## Security Tests

Test:

- Unauthorized access
- Cross-organization access
- Role violations
- Invalid tokens
- Injection attempts
- Rate limits
- Secret exposure

## Privacy Tests

Test:

```text
Developer identity
       ↓
AI Gateway
       ↓
MUST NOT APPEAR
```

---

# 60. API Acceptance Criteria

The API implementation is complete when:

- [ ] Authentication endpoints work.
- [ ] RBAC is enforced.
- [ ] Organization isolation works.
- [ ] Project APIs work.
- [ ] Team APIs work.
- [ ] Repository APIs work.
- [ ] Provider connections work.
- [ ] Provider webhooks work.
- [ ] Raw events are preserved.
- [ ] Duplicate provider events are rejected/deduplicated.
- [ ] Canonical events are generated.
- [ ] Analytics APIs operate on canonical data.
- [ ] Engineering Health APIs work.
- [ ] Individual productivity APIs do not exist.
- [ ] AI requests pass through the AI Gateway.
- [ ] Developer identity is removed from cloud-AI requests.
- [ ] AI failure does not break core analytics.
- [ ] Offline analytics remain available.
- [ ] API errors follow a consistent format.
- [ ] Pagination is implemented.
- [ ] Rate limiting is implemented.
- [ ] Audit logging is implemented.
- [ ] API documentation is generated.
- [ ] Unit tests pass.
- [ ] Integration tests pass.
- [ ] Security tests pass.
- [ ] Privacy tests pass.

---

# 61. OpenAPI Documentation

FastAPI should generate:

```text
/api/docs
/api/redoc
/openapi.json
```

The OpenAPI specification must remain synchronized with the implementation.

---

# 62. API Change Management

Any breaking API change must update:

```text
API_SPECIFICATION.md
DATABASE_SCHEMA.md
SYSTEM_ARCHITECTURE.md
Frontend API clients
Backend tests
Acceptance tests
```

API changes must be reviewed before implementation when they affect locked architecture.

---

# 63. Locked API Constraints

The following rules are mandatory:

```text
1. All protected APIs require authentication.

2. Authorization must be enforced server-side.

3. Organization-level data isolation is mandatory.

4. Raw provider events must be preserved.

5. Canonical events must be used for cross-provider analytics.

6. Individual productivity scoring APIs are prohibited.

7. Developer identity must never be sent to cloud AI.

8. Frontend must not directly call external LLM providers.

9. Frontend must not directly access PostgreSQL.

10. Provider-specific logic must remain inside adapters.

11. AI must not be required for core analytics.

12. Core analytics must continue in offline mode.

13. Provider events must be idempotently processed.

14. Sensitive credentials must never be returned by APIs.

15. All major API changes must be documented.
```

---

# 64. Final API Structure

```text
/api/v1
│
├── /auth
│   ├── /login
│   ├── /logout
│   ├── /refresh
│   └── /me
│
├── /organizations
│
├── /users
│
├── /roles
│
├── /teams
│
├── /projects
│
├── /repositories
│
├── /providers
│
├── /provider-connections
│
├── /webhooks
│
├── /raw-events
│
├── /events
│
├── /metrics
│
├── /analytics
│   ├── /dashboard
│   └── /trends
│
├── /ml
│   ├── /predictions
│   ├── /models
│   ├── /train
│   └── /features
│
├── /health
│   ├── /engineering
│   └── /engineering/history
│
├── /insights
│
├── /configuration
│
├── /audit-logs
│
├── /jobs
│
└── /health
```

---

# 65. Relationship With Other Documents

```text
PROJECT_CONTEXT.md
        ↓
PRD.md
        ↓
SYSTEM_ARCHITECTURE.md
        ↓
DATABASE_SCHEMA.md
        ↓
API_SPECIFICATION.md
        ↓
DATA_FLOW.md
        ↓
AI_DATA_BOUNDARY.md
        ↓
AGENTS.md
        ↓
TASKS.md
        ↓
ACCEPTANCE_TESTS.md
```

`API_SPECIFICATION.md` is the **communication contract** between the CodeSense frontend, backend services, integrations, analytics engine, and AI gateway.

It must remain synchronized with the database schema and system architecture throughout implementation.