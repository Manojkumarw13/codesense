# CodeSense — Implementation Tasks

**Document Status:** Draft / Editable  
**Version:** 1.0  
**Project:** CodeSense  
**Execution Model:** Sequential / Phase-Based  
**Primary Goal:** Build CodeSense from project foundation → core platform → integrations → analytics → Engineering Health → AI → security → testing → deployment.

---

# 1. How to Use This Document

Tasks must be completed **chronologically** unless a dependency explicitly allows parallel work.

Task status:

```text
[ ] NOT STARTED
[~] IN PROGRESS
[x] COMPLETED
[!] BLOCKED
[-] DEFERRED
```

Each task should have:

- A clear objective
- A defined dependency
- An implementation output
- Tests where applicable
- Documentation updates where required

---

# 2. Task Execution Rules

Before starting any task:

```text
Read Task
   ↓
Check Dependencies
   ↓
Read Relevant Documentation
   ↓
Inspect Existing Code
   ↓
Implement
   ↓
Test
   ↓
Review
   ↓
Mark Complete
```

Do not skip a prerequisite task merely because the next task appears easier.

---

# 3. Locked Requirements

All tasks must preserve these requirements:

```text
1. Raw provider events remain untouched.

2. Raw events remain available for reprocessing.

3. Canonical data is the cross-provider analytical layer.

4. Analytics primarily operate on canonical data.

5. Individual productivity scores do not exist.

6. Individual operational metrics require appropriate
   privacy and access controls.

7. Developer identity must never be sent to a cloud LLM.

8. Secrets and credentials must never be sent to AI.

9. Raw provider payloads must never be sent directly
   to a cloud LLM.

10. All external AI communication passes through
    the AI Gateway.

11. Core analytics continue to work offline.

12. Cloud AI is optional for core functionality.

13. Provider events must be processed idempotently.

14. Failed processing must not destroy raw events.

15. Organization and role-level access control is mandatory.
```

---

# PHASE 0 — Project Definition & Repository Setup

## P0.1 — Finalize Project Context

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** None

Tasks:

- [ ] Review project problem statement.
- [ ] Review target users.
- [ ] Review project scope.
- [ ] Review locked requirements.
- [ ] Identify MVP scope.
- [ ] Record final decisions in `PROJECT_CONTEXT.md`.

**Output:**

```text
PROJECT_CONTEXT.md
```

---

## P0.2 — Freeze Core Requirements

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P0.1

Tasks:

- [ ] Review PRD.
- [ ] Review conflict-resolution decisions.
- [ ] Confirm offline behavior.
- [ ] Confirm AI privacy requirements.
- [ ] Confirm analytics requirements.
- [ ] Confirm no individual productivity scoring.
- [ ] Mark confirmed requirements as locked.

**Output:**

```text
Locked requirements section in project documentation
```

---

## P0.3 — Initialize Git Repository

**Status:** [x] COMPLETED  
**Priority:** Critical  
**Depends on:** P0.2

Tasks:

- [x] Initialize repository.
- [x] Create `.gitignore`.
- [x] Create README.
- [x] Create branch strategy (main).
- [x] Configure commit conventions.

---

## P0.4 — Create Project Directory Structure

**Status:** [x] COMPLETED  
**Priority:** Critical  
**Depends on:** P0.3

Create:

```text
codesense/
├── backend/
├── frontend/
├── migrations/ (under database/)
├── tests/
├── scripts/
├── docker/
├── docs/
└── README.md
```

---

## P0.5 — Create Documentation Set

**Status:** [x] COMPLETED  
**Priority:** Critical  
**Depends on:** P0.4

Create:

```text
docs/
├── PRD.md
├── SYSTEM_ARCHITECTURE.md
├── DATABASE_SCHEMA.md
├── API_SPECIFICATION.md
├── DATA_FLOW.md
├── AI_DATA_BOUNDARY.md
├── AGENTS.md
├── TASKS.md
└── ACCEPTANCE_TESTS.md
```

---

# PHASE 1 — Development Environment

## P1.1 — Backend Environment

**Status:** [x] COMPLETED  
**Priority:** Critical  
**Depends on:** P0.4

Tasks:

- [x] Set up Python environment.
- [x] Install FastAPI.
- [x] Install Pydantic.
- [x] Install SQLAlchemy.
- [x] Install Alembic.
- [x] Configure development server.
- [x] Configure linting.
- [x] Configure formatting.
- [x] Configure type checking.

---

## P1.2 — Frontend Environment

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P0.4

Tasks:

- [ ] Initialize React application.
- [ ] Configure TypeScript.
- [ ] Configure routing.
- [ ] Configure API client.
- [ ] Configure frontend testing.

---

## P1.3 — Database Environment

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P1.1

Tasks:

- [ ] Set up PostgreSQL.
- [ ] Create development database.
- [ ] Configure connection string.
- [ ] Test database connectivity.

---

## P1.4 — Redis / Background Worker Environment

**Status:** [ ]  
**Priority:** High  
**Depends on:** P1.1

Tasks:

- [ ] Set up Redis.
- [ ] Configure worker framework.
- [ ] Create test background job.
- [ ] Verify queue communication.

---

## P1.5 — Docker Development Environment

**Status:** [ ]  
**Priority:** High  
**Depends on:** P1.1, P1.2, P1.3, P1.4

Create:

```text
docker-compose.yml
```

Services:

```text
frontend
backend
postgres
redis
worker
```

---

# PHASE 2 — Backend Foundation

## P2.1 — FastAPI Application

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P1.1

Tasks:

- [ ] Create FastAPI application.
- [ ] Configure application settings.
- [ ] Add API versioning.
- [ ] Add `/api/v1` router.
- [ ] Add startup/shutdown lifecycle.
- [ ] Add structured error handling.

---

## P2.2 — Configuration System

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P2.1

Implement configuration for:

```text
DATABASE_URL
REDIS_URL
JWT_SECRET
AI_PROVIDER
AI_MODEL
ENVIRONMENT
LOG_LEVEL
```

Tasks:

- [ ] Create settings model.
- [ ] Create `.env.example`.
- [ ] Prevent secrets from being committed.
- [ ] Validate required configuration.

---

## P2.3 — Logging

**Status:** [ ]  
**Priority:** High  
**Depends on:** P2.1

Tasks:

- [ ] Implement structured logging.
- [ ] Add request IDs.
- [ ] Add job IDs.
- [ ] Add event IDs.
- [ ] Add error codes.
- [ ] Prevent secret logging.

---

## P2.4 — Error Handling

**Status:** [ ]  
**Priority:** High  
**Depends on:** P2.1

Implement:

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

---

# PHASE 3 — Database Foundation

## P3.1 — SQLAlchemy Base

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P2.1

Tasks:

- [ ] Configure SQLAlchemy.
- [ ] Create base model.
- [ ] Configure sessions.
- [ ] Configure transaction handling.

---

## P3.2 — Alembic

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P3.1

Tasks:

- [ ] Initialize Alembic.
- [ ] Configure migrations.
- [ ] Test migration generation.
- [ ] Test migration execution.

---

## P3.3 — Organization Model

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P3.2

Implement:

```text
organizations
```

---

## P3.4 — User Model

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P3.3

Implement:

```text
users
```

---

## P3.5 — Roles & Permissions

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P3.4

Implement:

```text
roles
permissions
user_roles
```

---

## P3.6 — Team Models

**Status:** [ ]  
**Priority:** High  
**Depends on:** P3.5

Implement:

```text
teams
team_members
```

---

## P3.7 — Project Models

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P3.6

Implement:

```text
projects
project_members
```

---

## P3.8 — Repository Models

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P3.7

Implement:

```text
repositories
```

---

## P3.9 — Provider Models

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P3.8

Implement:

```text
providers
provider_connections
```

Credentials must be represented through secure references rather than exposed secrets.

---

# PHASE 4 — Authentication & Authorization

## P4.1 — Authentication System

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P3.5

Implement:

```text
POST /api/v1/auth/login
POST /api/v1/auth/logout
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
```

---

## P4.2 — Password / Credential Security

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P4.1

Tasks:

- [ ] Secure password hashing.
- [ ] Credential validation.
- [ ] Token expiration.
- [ ] Refresh-token handling.
- [ ] Failed-login protection.

---

## P4.3 — RBAC

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P4.1

Implement:

```text
Authentication
      ↓
Organization
      ↓
Role
      ↓
Permission
      ↓
Resource
```

---

## P4.4 — Organization Isolation

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P4.3

Test that:

```text
Organization A
    X
Organization B data
```

cannot occur.

---

# PHASE 5 — Core CRUD APIs

## P5.1 — Organization APIs

**Status:** [ ]  
**Depends on:** P4.4

Implement:

```text
GET    /organizations/{id}
PATCH  /organizations/{id}
```

---

## P5.2 — User APIs

**Status:** [ ]  
**Depends on:** P4.4

Implement:

```text
GET    /users
GET    /users/{id}
POST   /users
PATCH  /users/{id}
POST   /users/{id}/disable
```

---

## P5.3 — Team APIs

**Status:** [ ]  
**Depends on:** P5.2

Implement:

```text
GET    /teams
GET    /teams/{id}
POST   /teams
PATCH  /teams/{id}
DELETE /teams/{id}
```

---

## P5.4 — Project APIs

**Status:** [ ]  
**Depends on:** P5.3

Implement:

```text
GET    /projects
GET    /projects/{id}
POST   /projects
PATCH  /projects/{id}
POST   /projects/{id}/archive
```

---

## P5.5 — Repository APIs

**Status:** [ ]  
**Depends on:** P5.4

Implement repository management endpoints.

---

# PHASE 6 — Provider Integration Framework

## P6.1 — Provider Adapter Interface

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P5.5

Create:

```text
ProviderAdapter
```

with capabilities for:

```text
authenticate()
validate_connection()
fetch_events()
handle_webhook()
normalize_event()
```

---

## P6.2 — Provider Registry

**Status:** [ ]  
**Priority:** High  
**Depends on:** P6.1

Implement provider discovery and registration.

---

## P6.3 — Provider Connection API

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P6.2

Implement:

```text
GET  /providers
GET  /provider-connections
GET  /provider-connections/{id}
POST /provider-connections
POST /provider-connections/{id}/validate
POST /provider-connections/{id}/sync
```

---

# PHASE 7 — First Provider Integration

## P7.1 — Implement Primary Source-Control Provider

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P6.3

Implement the first supported provider.

Provider:

```text
[ EDIT: GitHub / GitLab / Bitbucket ]
```

---

## P7.2 — Provider Authentication

**Status:** [ ]  
**Depends on:** P7.1

Implement secure provider authentication.

---

## P7.3 — Repository Synchronization

**Status:** [ ]  
**Depends on:** P7.2

Implement:

```text
Provider API
    ↓
Sync
    ↓
Events
```

---

## P7.4 — Webhook Support

**Status:** [ ]  
**Depends on:** P7.2

Implement:

```text
POST /api/v1/webhooks/{provider}/{connection_id}
```

---

# PHASE 8 — Raw Event Ingestion

## P8.1 — Raw Event Table

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P3.9

Implement the raw-event database model.

---

## P8.2 — Raw Event Storage

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P8.1

Tasks:

- [ ] Store original payload.
- [ ] Store provider event ID.
- [ ] Store connection ID.
- [ ] Store event type.
- [ ] Store received timestamp.
- [ ] Store processing status.

---

## P8.3 — Event Deduplication

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P8.2

Implement:

```text
provider_connection_id
+
provider_event_id
```

uniqueness.

---

## P8.4 — Raw Event Immutability

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P8.2

Verify that processing cannot modify the original payload.

---

# PHASE 9 — Event Processing Pipeline

## P9.1 — Processing Queue

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P8.3

Implement:

```text
Raw Event
    ↓
Queue
    ↓
Worker
```

---

## P9.2 — Event Classification

**Status:** [ ]  
**Depends on:** P9.1

Classify incoming provider events.

---

## P9.3 — Event Validation

**Status:** [ ]  
**Depends on:** P9.2

Validate:

- Required fields
- Event type
- Timestamp
- Provider identifiers
- Entity references

---

## P9.4 — Retry System

**Status:** [ ]  
**Priority:** High  
**Depends on:** P9.3

Implement:

```text
Failure
 ↓
Retry
 ↓
Retry
 ↓
Dead Letter / Manual Review
```

---

# PHASE 10 — Canonical Data Layer

## P10.1 — Canonical Event Model

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P9.3

Create canonical event abstraction.

---

## P10.2 — Canonical Pull Request Event

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P10.1

Support:

```text
Pull Request
Merge Request
```

under a common canonical model.

---

## P10.3 — Canonical Commit Event

**Status:** [ ]  
**Priority:** High  
**Depends on:** P10.1

---

## P10.4 — Canonical Review Event

**Status:** [ ]  
**Priority:** High  
**Depends on:** P10.1

---

## P10.5 — Canonical Deployment Event

**Status:** [ ]  
**Priority:** High  
**Depends on:** P10.1

---

## P10.6 — Canonical Issue Event

**Status:** [ ]  
**Priority:** High  
**Depends on:** P10.1

---

## P10.7 — Raw-to-Canonical Lineage

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P10.2–P10.6

Every canonical event must be traceable to its raw event.

---

# PHASE 11 — Second Provider Integration

## P11.1 — Add Second Provider

**Status:** [ ]  
**Priority:** High  
**Depends on:** P10.7

Provider:

```text
[ EDIT ]
```

---

## P11.2 — Map Provider Events

**Status:** [ ]  
**Depends on:** P11.1

Map provider-specific events into existing canonical models.

---

## P11.3 — Cross-Provider Validation

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P11.2

Verify that analytics can consume both providers without provider-specific analytics logic.

---

# PHASE 12 — Analytics Engine

## P12.1 — Analytics Service

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P10.7

Create analytics service layer.

---

## P12.2 — Metric Definition System

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P12.1

Implement:

```text
metrics
metric_definitions
metric_values
```

---

## P12.3 — Delivery Metrics

**Status:** [ ]  
**Priority:** High  
**Depends on:** P12.2

Implement approved delivery metrics such as:

```text
Deployment Frequency
Lead Time
```

---

## P12.4 — Review Metrics

**Status:** [ ]  
**Priority:** High  
**Depends on:** P12.2

Implement:

```text
Review Cycle Time
PR/MR throughput
```

---

## P12.5 — Quality Metrics

**Status:** [ ]  
**Priority:** High  
**Depends on:** P12.2

Implement approved quality indicators.

---

## P12.6 — Reliability Metrics

**Status:** [ ]  
**Priority:** High  
**Depends on:** P12.2

Implement approved reliability indicators.

---

## P12.7 — Time-Series Aggregation

**Status:** [ ]  
**Priority:** High  
**Depends on:** P12.3–P12.6

Support:

```text
Daily
Weekly
Monthly
Custom period
```

---

## P12.8 — Trend Detection

**Status:** [ ]  
**Priority:** High  
**Depends on:** P12.7

Detect:

```text
Improving
Declining
Stable
Anomalous
```

---

# PHASE 13 — Engineering Health

## P13.1 — Define Engineering Health Formula

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P12.8

Document:

- Components
- Weights
- Normalization
- Thresholds
- Minimum data requirements

---

## P13.2 — Engineering Health Calculation

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P13.1

Implement health calculation.

---

## P13.3 — Historical Health Scores

**Status:** [ ]  
**Depends on:** P13.2

Store historical values.

---

## P13.4 — Health API

**Status:** [ ]  
**Depends on:** P13.3

Implement:

```text
GET /api/v1/health/engineering
GET /api/v1/health/engineering/history
```

---

## P13.5 — Productivity-Safety Validation

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P13.2

Verify:

```text
No individual productivity score
No hidden productivity formula
No individual ranking
```

---

# PHASE 14 — Dashboard

## P14.1 — Application Shell

**Status:** [ ]  
**Priority:** High  
**Depends on:** P5.4

Create:

```text
Navigation
Authentication state
Layout
Theme
Error handling
Loading states
```

---

## P14.2 — Overview Dashboard

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P13.4

Display:

```text
Engineering Health
Key Metrics
Trends
Alerts / Insights
```

---

## P14.3 — Project Dashboard

**Status:** [ ]  
**Depends on:** P14.2

---

## P14.4 — Team Dashboard

**Status:** [ ]  
**Depends on:** P14.2

Team-level analytics only.

---

## P14.5 — Trend Visualization

**Status:** [ ]  
**Depends on:** P14.2

Display:

```text
Metric trends
Engineering Health trends
Delivery trends
Quality trends
Reliability trends
```

---

# PHASE 15 — AI Foundation

## P15.1 — AI Service

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P12.8

Create:

```text
backend/app/ai/
```

---

## P15.2 — AI Context Builder

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P15.1

Implement:

```text
Analytics
 ↓
Context Selection
 ↓
Aggregation
 ↓
AI Context
```

---

## P15.3 — Identity Sanitizer

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P15.2

Ensure:

```text
Developer Identity
       ↓
REMOVED
```

before cloud AI.

---

## P15.4 — Secret Detector

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P15.2

Detect:

```text
API keys
Tokens
Passwords
Private keys
Credentials
```

---

## P15.5 — Raw Payload Blocker

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P15.2

Ensure raw provider payloads cannot enter cloud AI context.

---

## P15.6 — AI Policy Engine

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P15.3–P15.5

Implement allow/block decisions.

Default:

```text
Unknown Data → BLOCK
```

---

# PHASE 16 — AI Gateway

## P16.1 — AI Gateway Interface

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P15.6

Create provider-independent interface.

---

## P16.2 — Local LLM Adapter

**Status:** [ ]  
**Priority:** High  
**Depends on:** P16.1

Support optional local AI.

---

## P16.3 — Cloud LLM Adapter

**Status:** [ ]  
**Priority:** High  
**Depends on:** P16.1

Support approved cloud AI provider.

The exact provider/model should remain configurable.

---

## P16.4 — AI Provider Routing

**Status:** [ ]  
**Depends on:** P16.2, P16.3

Implement:

```text
Configured Provider
       ↓
AI Gateway
       ↓
Local / Cloud
```

---

## P16.5 — AI Response Validation

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P16.4

Validate:

- Response schema
- Unexpected data
- Unsupported claims
- Sensitive output
- Length
- Required fields

---

# PHASE 17 — AI Insights

## P17.1 — Insight Model

**Status:** [ ]  
**Priority:** High  
**Depends on:** P16.5

Implement AI insight storage.

---

## P17.2 — Generate Insight API

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P17.1

Implement:

```text
POST /api/v1/insights/generate
```

---

## P17.3 — Insight Retrieval API

**Status:** [ ]  
**Depends on:** P17.1

Implement:

```text
GET /api/v1/insights
GET /api/v1/insights/{id}
```

---

## P17.4 — Engineering Trend Insights

**Status:** [ ]  
**Priority:** High  
**Depends on:** P17.3

Generate explanations for:

```text
Metric changes
Engineering Health changes
Delivery trends
Review trends
Quality trends
Reliability trends
```

---

# PHASE 18 — Prompt Injection Protection

## P18.1 — Treat Provider Text as Untrusted

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P15.2

Protect against:

```text
PR title injection
Commit message injection
Issue description injection
Comment injection
```

---

## P18.2 — Prompt Boundary

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P18.1

Ensure provider text cannot override:

```text
System instructions
Privacy rules
AI policies
Security rules
```

---

## P18.3 — Prompt Injection Tests

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P18.2

Create malicious test payloads and verify blocking/containment.

---

# PHASE 19 — Offline Mode

## P19.1 — Detect Connectivity State

**Status:** [ ]  
**Priority:** High  
**Depends on:** P1.5

---

## P19.2 — Offline Analytics

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P12.8

Verify analytics operate entirely from locally available data.

---

## P19.3 — Offline Engineering Health

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P13.4

Verify Engineering Health remains functional offline.

---

## P19.4 — Cloud AI Offline Failure

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P16.3

Cloud AI should return a controlled unavailable state.

---

## P19.5 — Local AI Offline Mode

**Status:** [ ]  
**Priority:** Optional  
**Depends on:** P16.2

If local LLM is configured:

```text
Offline
 ↓
AI Gateway
 ↓
Local LLM
```

---

## P19.6 — Reconnection Synchronization

**Status:** [ ]  
**Priority:** High  
**Depends on:** P7.3, P8.3

When connectivity returns:

```text
Checkpoint
 ↓
Fetch Missing Events
 ↓
Deduplicate
 ↓
Process
 ↓
Update Analytics
```

---

# PHASE 20 — Audit & Security

## P20.1 — Audit Log System

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P4.3

---

## P20.2 — Security Event Logging

**Status:** [ ]  
**Priority:** High  
**Depends on:** P20.1

Track:

```text
Authentication failures
Authorization failures
AI privacy blocks
Provider failures
Suspicious requests
```

---

## P20.3 — Rate Limiting

**Status:** [ ]  
**Priority:** High  
**Depends on:** P2.1

Apply limits to:

```text
Authentication
AI generation
Expensive analytics
Webhooks
Administrative APIs
```

---

## P20.4 — Webhook Security

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P7.4

Implement:

```text
Signature verification
Replay protection
Request validation
Rate limiting
```

---

## P20.5 — Security Headers

**Status:** [ ]  
**Priority:** Medium  
**Depends on:** P2.1

---

# PHASE 21 — Testing

## P21.1 — Unit Test Framework

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P2.1

---

## P21.2 — Backend Unit Tests

**Status:** [ ]  
**Depends on:** P21.1

Cover:

```text
Services
Repositories
Validators
Canonical transformations
Analytics
Health calculations
AI filtering
```

---

## P21.3 — API Tests

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P5.5

Test:

```text
Authentication
Authorization
CRUD
Pagination
Errors
Organization isolation
```

---

## P21.4 — Provider Integration Tests

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P7.4

---

## P21.5 — Event Pipeline Tests

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P9.4

Test:

```text
Ingestion
Deduplication
Queue
Processing
Retry
Failure
Canonical transformation
```

---

## P21.6 — Analytics Tests

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P12.8

---

## P21.7 — Engineering Health Tests

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P13.2

---

## P21.8 — AI Privacy Tests

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P16.5

Verify:

```text
Developer identity → BLOCKED
Secrets → BLOCKED
Raw payload → BLOCKED
AI-safe metrics → ALLOWED
Unknown data → BLOCKED
```

---

## P21.9 — Prompt Injection Tests

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P18.3

---

## P21.10 — Offline Tests

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P19.4

---

## P21.11 — End-to-End Tests

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P21.1–P21.10

Test:

```text
Provider
 ↓
Webhook
 ↓
Raw Event
 ↓
Canonical Event
 ↓
Analytics
 ↓
Engineering Health
 ↓
Dashboard
 ↓
AI Insight
```

---

# PHASE 22 — Performance

## P22.1 — Database Index Review

**Status:** [ ]  
**Priority:** High  
**Depends on:** P21.6

Review:

```text
Foreign keys
Event IDs
Organization IDs
Project IDs
Timestamps
Provider IDs
```

---

## P22.2 — API Performance

**Status:** [ ]  
**Depends on:** P21.3

Measure:

```text
Latency
Throughput
Concurrent users
```

---

## P22.3 — Event Processing Performance

**Status:** [ ]  
**Depends on:** P21.5

Measure:

```text
Events/second
Queue latency
Worker throughput
Retry rate
```

---

## P22.4 — Analytics Performance

**Status:** [ ]  
**Depends on:** P21.6

Optimize expensive analytical queries.

---

# PHASE 23 — Observability

## P23.1 — Application Metrics

**Status:** [ ]  
**Depends on:** P20.2

Monitor:

```text
API latency
Error rate
Request count
```

---

## P23.2 — Event Pipeline Metrics

**Status:** [ ]  
**Depends on:** P22.3

Monitor:

```text
Events received
Events processed
Events failed
Queue depth
Processing latency
```

---

## P23.3 — Provider Health

**Status:** [ ]  
**Depends on:** P23.2

Monitor:

```text
Connection status
Last synchronization
Failure rate
Webhook health
```

---

## P23.4 — AI Health

**Status:** [ ]  
**Depends on:** P16.5

Monitor:

```text
AI requests
AI failures
AI latency
Privacy blocks
Provider availability
```

---

# PHASE 24 — Deployment

## P24.1 — Production Docker Configuration

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P23.4

---

## P24.2 — Production PostgreSQL

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P24.1

Configure:

```text
Backups
Connection limits
Indexes
Security
Monitoring
```

---

## P24.3 — Reverse Proxy

**Status:** [ ]  
**Priority:** High  
**Depends on:** P24.1

---

## P24.4 — TLS

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P24.3

---

## P24.5 — Environment Configuration

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P24.4

Separate:

```text
Development
Testing
Production
```

---

# PHASE 25 — Backup & Recovery

## P25.1 — Database Backup

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P24.2

---

## P25.2 — Backup Restoration Test

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P25.1

A backup is not considered valid until restoration has been tested.

---

## P25.3 — Raw Event Recovery

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P25.1

Verify raw events can be used to reconstruct canonical data.

---

# PHASE 26 — Documentation

## P26.1 — Update API Documentation

**Status:** [ ]  
**Depends on:** P21.3

---

## P26.2 — Update Database Documentation

**Status:** [ ]  
**Depends on:** P21.6

---

## P26.3 — Update Data Flow

**Status:** [ ]  
**Depends on:** P21.5

---

## P26.4 — Update AI Boundary

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P21.8

---

## P26.5 — Update AGENTS.md

**Status:** [ ]  
**Depends on:** P26.4

Document any newly discovered implementation constraints.

---

## P26.6 — Developer Setup Guide

**Status:** [ ]  
**Priority:** High  
**Depends on:** P24.1

Create:

```text
docs/DEVELOPMENT_SETUP.md
```

---

## P26.7 — Deployment Guide

**Status:** [ ]  
**Priority:** High  
**Depends on:** P24.5

Create:

```text
docs/DEPLOYMENT.md
```

---

# PHASE 27 — Final Security & Privacy Audit

## P27.1 — Authentication Audit

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P26.7

---

## P27.2 — Authorization Audit

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P27.1

---

## P27.3 — Organization Isolation Audit

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P27.2

---

## P27.4 — AI Privacy Audit

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P27.3

Verify:

```text
Developer identity
Secrets
Raw events
Personal information
Individual productivity data
```

cannot cross the cloud AI boundary.

---

## P27.5 — Individual Productivity Audit

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P27.4

Search codebase and database schema for prohibited concepts.

Examples:

```text
productivity_score
developer_score
employee_score
individual_productivity
```

---

# PHASE 28 — Final Acceptance Testing

## P28.1 — Functional Acceptance

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P27.5

Verify:

```text
[ ] Authentication
[ ] Projects
[ ] Teams
[ ] Repositories
[ ] Provider integration
[ ] Event ingestion
[ ] Canonical processing
[ ] Analytics
[ ] Engineering Health
[ ] Dashboard
[ ] AI insights
```

---

## P28.2 — Privacy Acceptance

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P28.1

Verify:

```text
[ ] Developer identity blocked
[ ] Secrets blocked
[ ] Credentials blocked
[ ] Raw provider payload blocked
[ ] Unknown data blocked
[ ] Individual productivity scoring absent
```

---

## P28.3 — Offline Acceptance

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P28.2

Verify:

```text
[ ] Core analytics work offline
[ ] Engineering Health works offline
[ ] Dashboard works with local data
[ ] Cloud AI failure is graceful
[ ] Reconnection synchronization works
```

---

## P28.4 — Reliability Acceptance

**Status:** [ ]  
**Priority:** High  
**Depends on:** P28.3

Test:

```text
Provider failure
Database failure
Worker failure
AI provider failure
Network failure
Duplicate events
Malformed events
```

---

## P28.5 — Final End-to-End Acceptance

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P28.4

Run:

```text
External Provider
       ↓
Provider Adapter
       ↓
Webhook
       ↓
Raw Event
       ↓
Queue
       ↓
Worker
       ↓
Canonical Event
       ↓
Analytics
       ↓
Engineering Health
       ↓
Dashboard
       ↓
Sanitized AI Context
       ↓
AI Gateway
       ↓
AI Insight
       ↓
Dashboard
```

---

# PHASE 29 — MVP Release

## P29.1 — MVP Feature Freeze

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P28.5

Freeze the MVP feature set.

No new major features after this point without explicit approval.

---

## P29.2 — Production Readiness Review

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P29.1

Review:

```text
Security
Privacy
Performance
Reliability
Backup
Monitoring
Documentation
Testing
```

---

## P29.3 — MVP Release

**Status:** [ ]  
**Priority:** Critical  
**Depends on:** P29.2

---

# 4. MVP Scope

The first usable CodeSense MVP should prioritize:

```text
1. Authentication
2. Organizations
3. Teams
4. Projects
5. Repositories
6. One primary provider integration
7. Raw event ingestion
8. Canonical event processing
9. Core analytics
10. Engineering Health Score
11. Dashboard
12. AI Gateway
13. AI privacy boundary
14. Basic AI insights
15. Offline core analytics
16. Audit logging
17. Testing
```

Do not delay the MVP for non-essential integrations.

---

# 5. Future Features

These should remain outside the initial MVP unless explicitly promoted:

```text
[ ] Additional source-control providers
[ ] Additional project-management providers
[ ] Advanced incident integrations
[ ] Advanced observability integrations
[ ] Advanced local AI
[ ] Advanced anomaly detection
[ ] Advanced forecasting
[ ] Advanced reporting
[ ] Enterprise SSO
[ ] Advanced data exports
[ ] Advanced alerting
```

---

# 6. Dependency Map

```text
Foundation
    ↓
Database
    ↓
Authentication
    ↓
Core APIs
    ↓
Provider Framework
    ↓
Raw Events
    ↓
Processing Pipeline
    ↓
Canonical Layer
    ↓
Analytics
    ↓
Engineering Health
    ↓
Dashboard
    ↓
AI Boundary
    ↓
AI Gateway
    ↓
AI Insights
    ↓
Offline Mode
    ↓
Security
    ↓
Testing
    ↓
Performance
    ↓
Deployment
    ↓
Acceptance
    ↓
MVP
```

---

# 7. Parallel Work Opportunities

After foundational dependencies are complete, some tasks can proceed in parallel.

```text
                 Canonical Layer
                       │
          ┌────────────┼────────────┐
          ↓            ↓            ↓
      Analytics     Provider 2    Frontend
          │
          ↓
    Health Engine
          │
          ↓
       Dashboard
```

AI development can begin once the analytics contracts and AI boundary are stable:

```text
Analytics Contract
       │
       ├──── AI Context Builder
       │
       └──── Dashboard Analytics
```

---

# 8. Task Priority Definitions

```text
CRITICAL
Required for core architecture or MVP.

HIGH
Required for a complete production-quality feature.

MEDIUM
Important but can follow the MVP.

LOW
Optional enhancement.

FUTURE
Not part of current implementation scope.
```

---

# 9. Task Completion Rules

A task may be marked `[x]` only when:

```text
[ ] Implementation complete
[ ] Relevant tests pass
[ ] Security requirements checked
[ ] Privacy requirements checked
[ ] Offline impact checked
[ ] Documentation updated where required
[ ] No locked requirement violated
```

---

# 10. Blocked Task Rules

If a task cannot proceed:

```text
[!] BLOCKED
```

Record:

```text
Blocked By:
Reason:
Required Decision:
Next Action:
```

Example:

```text
[!] P13.1

Blocked By:
Engineering Health scoring definition.

Reason:
Formula has not been finalized.

Required Decision:
Confirm metric weights and normalization.

Next Action:
Finalize Engineering Health specification.
```

Do not implement an arbitrary solution just to remove the blocked status.

---

# 11. Change Management

If a requirement changes:

```text
Requirement Change
      ↓
Update PRD
      ↓
Check Architecture
      ↓
Check Database
      ↓
Check API
      ↓
Check Data Flow
      ↓
Check AI Boundary
      ↓
Update AGENTS.md
      ↓
Update TASKS.md
      ↓
Implement
```

Do not update only the task list.

---

# 12. Final Project Completion Checklist

```text
FOUNDATION
[ ] Project repository
[ ] Documentation
[ ] Development environment
[ ] Docker environment

BACKEND
[ ] FastAPI
[ ] Configuration
[ ] Logging
[ ] Error handling

DATABASE
[ ] PostgreSQL
[ ] SQLAlchemy
[ ] Alembic
[ ] Core schema

AUTH
[ ] Authentication
[ ] RBAC
[ ] Organization isolation

CORE PLATFORM
[ ] Organizations
[ ] Users
[ ] Teams
[ ] Projects
[ ] Repositories

INTEGRATIONS
[ ] Provider framework
[ ] Primary provider
[ ] Webhooks
[ ] Synchronization

DATA PIPELINE
[ ] Raw events
[ ] Deduplication
[ ] Queue
[ ] Workers
[ ] Retry
[ ] Canonical events
[ ] Data lineage

ANALYTICS
[ ] Metrics
[ ] Aggregations
[ ] Trends
[ ] Analytics APIs

ENGINEERING HEALTH
[ ] Formula
[ ] Calculation
[ ] History
[ ] API
[ ] No productivity scoring

FRONTEND
[ ] Application shell
[ ] Dashboard
[ ] Project view
[ ] Team view
[ ] Trends

AI
[ ] Context Builder
[ ] Privacy Filter
[ ] Identity Sanitizer
[ ] Secret Detector
[ ] Raw Payload Blocker
[ ] AI Gateway
[ ] Local LLM option
[ ] Cloud LLM option
[ ] Response validation
[ ] AI Insights

OFFLINE
[ ] Offline analytics
[ ] Offline Engineering Health
[ ] Cloud AI graceful failure
[ ] Reconnection synchronization

SECURITY
[ ] Authentication audit
[ ] Authorization audit
[ ] Webhook security
[ ] Rate limiting
[ ] Audit logging
[ ] Secret protection

TESTING
[ ] Unit tests
[ ] API tests
[ ] Integration tests
[ ] Pipeline tests
[ ] Analytics tests
[ ] Health tests
[ ] Privacy tests
[ ] Prompt injection tests
[ ] Offline tests
[ ] E2E tests

OPERATIONS
[ ] Monitoring
[ ] Backups
[ ] Recovery testing
[ ] Production configuration
[ ] TLS
[ ] Deployment documentation

RELEASE
[ ] Final security audit
[ ] Final privacy audit
[ ] Final acceptance
[ ] MVP freeze
[ ] Production readiness
[ ] MVP release
```

---

# 13. Final CodeSense Build Flow

```text
                 ┌────────────────────┐
                 │ PROJECT DEFINITION  │
                 └──────────┬─────────┘
                            ↓
                 ┌────────────────────┐
                 │ DEV ENVIRONMENT    │
                 └──────────┬─────────┘
                            ↓
                 ┌────────────────────┐
                 │ BACKEND + DATABASE │
                 └──────────┬─────────┘
                            ↓
                 ┌────────────────────┐
                 │ AUTH + RBAC        │
                 └──────────┬─────────┘
                            ↓
                 ┌────────────────────┐
                 │ CORE APIs          │
                 └──────────┬─────────┘
                            ↓
                 ┌────────────────────┐
                 │ PROVIDER ADAPTERS  │
                 └──────────┬─────────┘
                            ↓
                 ┌────────────────────┐
                 │ RAW EVENT PIPELINE │
                 └──────────┬─────────┘
                            ↓
                 ┌────────────────────┐
                 │ CANONICAL DATA     │
                 └──────────┬─────────┘
                            ↓
                 ┌────────────────────┐
                 │ ANALYTICS ENGINE   │
                 └──────────┬─────────┘
                            ↓
                 ┌────────────────────┐
                 │ ENGINEERING HEALTH │
                 └──────────┬─────────┘
                            ↓
                 ┌────────────────────┐
                 │ DASHBOARD          │
                 └──────────┬─────────┘
                            ↓
                 ┌────────────────────┐
                 │ AI DATA BOUNDARY   │
                 └──────────┬─────────┘
                            ↓
                 ┌────────────────────┐
                 │ AI GATEWAY         │
                 └──────────┬─────────┘
                            ↓
                 ┌────────────────────┐
                 │ AI INSIGHTS        │
                 └──────────┬─────────┘
                            ↓
                 ┌────────────────────┐
                 │ OFFLINE + SECURITY │
                 └──────────┬─────────┘
                            ↓
                 ┌────────────────────┐
                 │ TEST + AUDIT       │
                 └──────────┬─────────┘
                            ↓
                 ┌────────────────────┐
                 │ DEPLOYMENT         │
                 └──────────┬─────────┘
                            ↓
                 ┌────────────────────┐
                 │ ACCEPTANCE         │
                 └──────────┬─────────┘
                            ↓
                 ┌────────────────────┐
                 │ CODESENSE MVP      │
                 └────────────────────┘
```

---

# 14. Relationship With Other Documents

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

`TASKS.md` is the **execution roadmap** for CodeSense.

The coding agent should use it to determine **what to implement next**, while `AGENTS.md` determines **how the implementation must be performed** and the other architecture documents determine **what the system must ultimately do**.

---

# PHASE 25 — Hybrid ML

## P25.1 — Feature Pipeline

**Status:** [ ]  
**Priority:** High  

Extract and store features for global/org/team scopes. No individual developer modeling.

---

## P25.2 — Model Training

**Status:** [ ]  
**Priority:** High  
**Depends on:** P25.1

Train models based on extracted features.

---

## P25.3 — Risk Prediction

**Status:** [ ]  
**Priority:** High  
**Depends on:** P25.2

Predict risks with mandatory evidence and confidence.

---

## P25.4 — ML Anomaly

**Status:** [ ]  
**Priority:** High  
**Depends on:** P25.2

Detect anomalies using Hybrid ML models.

---

## P25.5 — Fusion Engine

**Status:** [ ]  
**Priority:** High  
**Depends on:** P25.4

Merge Rules + Stats + ML for a consolidated prediction API.

---

## P25.6 — Infrastructure Setup (Redis, Workers)

**Status:** [ ]  
**Priority:** High  
**Depends on:** P25.5

Configure Redis and Workers for ML job execution.