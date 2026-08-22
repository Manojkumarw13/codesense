# CodeSense — System Architecture

**Document Status:** Draft / Editable  
**Version:** 1.0  
**Project:** CodeSense  
**Purpose:** Technical architecture specification for implementation and vibe coding

---

## 1. Architecture Overview

CodeSense is an engineering intelligence platform that collects software-development events from multiple development and delivery platforms, normalizes them into a canonical analytical model, processes them into engineering analytics, and presents actionable engineering insights through a unified dashboard.

The architecture is designed around these principles:

1. Provider-independent analytics
2. Raw-event preservation
3. Canonical analytical data
4. Privacy-preserving AI integration
5. Offline-first core functionality
6. Modular provider integrations
7. API-first backend
8. Secure role-based access
9. Testable and observable services
10. Scalable asynchronous processing

---

# 2. High-Level Architecture

```text
                    ┌─────────────────────────┐
                    │       Developers        │
                    │       Managers          │
                    │       Engineering       │
                    │       Leadership         │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │      CodeSense UI        │
                    │                          │
                    │ Dashboard                │
                    │ Analytics                │
                    │ Engineering Health       │
                    │ Insights                 │
                    │ Configuration            │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │       API Gateway        │
                    │ Authentication / RBAC    │
                    │ Rate Limiting            │
                    │ Request Validation       │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
     ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
     │ Integration    │ │ Analytics      │ │ AI / Insights  │
     │ Service        │ │ Service        │ │ Service        │
     └───────┬────────┘ └───────┬────────┘ └───────┬────────┘
             │                  │                  │
             ▼                  ▼                  ▼
     ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
     │ Raw Event      │ │ Canonical      │ │ AI Gateway     │
     │ Store          │ │ Analytical     │ │ / Privacy      │
     │                │ │ Layer          │ │ Boundary       │
     └───────┬────────┘ └───────┬────────┘ └───────┬────────┘
             │                  │                  │
             └──────────────────┼──────────────────┘
                                ▼
                    ┌─────────────────────────┐
                    │     PostgreSQL          │
                    │                         │
                    │ Operational Data        │
                    │ Canonical Data          │
                    │ Analytics               │
                    │ Configuration           │
                    └─────────────────────────┘
```

---

# 3. Major Architectural Layers

CodeSense is divided into the following layers:

```text
Presentation Layer
        ↓
API Layer
        ↓
Application / Service Layer
        ↓
Integration & Processing Layer
        ↓
Canonical Analytical Layer
        ↓
Persistence Layer
        ↓
Infrastructure Layer
```

---

# 4. Presentation Layer

## Responsibility

Provides the user-facing CodeSense interface.

## Major Components

### Dashboard

Displays:

- Engineering Health Score
- Engineering trends
- Delivery metrics
- Development activity
- Quality indicators
- Reliability indicators
- Team-level insights

### Analytics

Provides:

- Time-series analysis
- Provider comparisons
- Team/project analytics
- Engineering trends
- Custom filtering
- Drill-down analysis

### Insights

Displays:

- AI-generated insights
- Engineering recommendations
- Anomaly explanations
- Trend explanations
- Suggested actions

### Administration

Provides:

- User management
- Role management
- Provider configuration
- Project configuration
- AI configuration
- System configuration

---

# 5. API Layer

The API layer is the primary communication boundary between the frontend and backend.

## Responsibilities

- Authentication
- Authorization
- Request validation
- Response formatting
- API versioning
- Rate limiting
- Error handling
- Audit logging

## Example API Groups

```text
/api/v1/auth
/api/v1/users
/api/v1/projects
/api/v1/providers
/api/v1/events
/api/v1/analytics
/api/v1/health
/api/v1/insights
/api/v1/configuration
```

---

# 6. Authentication and Authorization

CodeSense must use role-based access control.

## Example Roles

```text
ADMIN
ENGINEERING_LEADER
ENGINEERING_MANAGER
TECH_LEAD
ANALYST
DEVELOPER
```

Permissions must be assigned based on role rather than hard-coded throughout the application.

## Requirements

- Secure authentication
- Password/session/token protection
- Role-based authorization
- Resource-level access control
- Audit logging
- Secure session handling

---

# 7. Integration Layer

The integration layer connects CodeSense to external development and delivery platforms.

## Provider Examples

```text
GitHub
GitLab
Jira
CI/CD platforms
Issue trackers
Code review platforms
Other supported engineering tools
```

The architecture must use an adapter-based integration model.

```text
Provider
   ↓
Provider Adapter
   ↓
Provider Event
   ↓
Raw Event Store
   ↓
Canonical Transformation
```

## Provider Adapter

Every provider integration should implement a common interface.

Example conceptual interface:

```text
ProviderAdapter

├── authenticate()
├── validate_connection()
├── fetch_events()
├── normalize_event()
├── handle_webhook()
└── get_provider_metadata()
```

This prevents provider-specific logic from spreading throughout the application.

---

# 8. Raw Event Layer

Raw provider events must be preserved without destructive modification.

```text
External Provider
       ↓
Raw Event Ingestion
       ↓
Raw Event Store
```

## Principle

The original provider event should remain available for:

- Auditing
- Reprocessing
- Debugging
- Future analytics
- Schema evolution
- Provider-specific analysis

Raw events must not be overwritten by canonical transformations.

---

# 9. Canonical Analytical Layer

The canonical layer converts provider-specific events into a provider-independent representation.

Example:

```text
GitHub Pull Request
GitLab Merge Request
          │
          ▼
Canonical Code Review Event
```

Similarly:

```text
GitHub Commit
GitLab Commit
          │
          ▼
Canonical Commit Event
```

## Purpose

The canonical layer enables:

- Cross-provider analytics
- Consistent metrics
- Provider-independent dashboards
- Unified querying
- Easier future integrations

---

# 10. Event Processing Pipeline

The main processing pipeline is:

```text
Provider
   ↓
Ingestion
   ↓
Validation
   ↓
Raw Event Storage
   ↓
Event Classification
   ↓
Canonical Transformation
   ↓
Canonical Storage
   ↓
Aggregation
   ↓
Analytics
   ↓
Engineering Health Score
   ↓
Dashboard / Insights
```

---

# 11. Event Processing Service

## Responsibilities

- Consume incoming events
- Validate schemas
- Deduplicate events
- Identify event type
- Transform provider-specific events
- Store canonical events
- Trigger analytics processing

## Processing requirements

The processor should be:

- Idempotent
- Retryable
- Observable
- Fault tolerant
- Provider independent

---

# 12. Analytics Service

The analytics service operates primarily on canonical data.

## Responsibilities

- Metric calculation
- Aggregation
- Trend detection
- Time-series analysis
- Cross-provider comparison
- Engineering health calculation

Analytics must not depend directly on provider-specific schemas wherever a canonical representation exists.

---

# 13. Engineering Health Score

The Engineering Health Score is a system-level engineering health indicator.

It should be calculated from approved engineering signals.

Conceptual model:

```text
Engineering Signals
       │
       ├── Delivery
       ├── Code Review
       ├── Quality
       ├── Reliability
       ├── Development Flow
       └── Other approved signals
                │
                ▼
        Metric Aggregation
                │
                ▼
       Engineering Health
                │
                ▼
       Dashboard / Trends
```

## Important restriction

CodeSense must not convert individual developer activity into an individual productivity score.

Individual operational metrics may exist where necessary, subject to privacy and access controls.

---

# 14. AI / Insight Service

AI is an optional intelligence layer rather than a dependency for core CodeSense functionality.

```text
Analytics
    ↓
Insight Preparation
    ↓
Privacy Filter
    ↓
AI Gateway
    ↓
Cloud / Local LLM
    ↓
Insight Validation
    ↓
CodeSense
```

---

# 15. AI Privacy Boundary

The AI gateway is a strict security boundary.

## Data allowed to AI

Only explicitly approved, privacy-safe analytical information should be sent to a cloud LLM.

Examples:

```text
Aggregated engineering metrics
Anonymized trends
System-level statistics
Non-identifying project information
```

## Data prohibited from cloud AI

```text
Developer identity
Personally identifying developer information
Sensitive individual-level data
Raw provider credentials
Access tokens
Secrets
Unfiltered provider payloads
```

### Critical rule

**Developer identity must never be sent to the cloud LLM.**

---

# 16. Offline Architecture

CodeSense must continue functioning when Internet connectivity is unavailable.

```text
                OFFLINE MODE

Provider Data
      ↓
Local Ingestion
      ↓
Raw Event Store
      ↓
Canonical Layer
      ↓
Analytics
      ↓
Engineering Health
      ↓
Dashboard
```

Cloud AI features may become unavailable.

```text
Offline
   │
   ├── Core Analytics       → AVAILABLE
   ├── Data Processing      → AVAILABLE
   ├── Dashboard            → AVAILABLE
   ├── Engineering Health  → AVAILABLE
   └── Cloud AI            → UNAVAILABLE
```

Core CodeSense functionality must not depend on cloud AI availability.

---

# 17. Data Storage Architecture

PostgreSQL is the primary relational data store.

Conceptual organization:

```text
PostgreSQL
│
├── Identity & Access
│
├── Projects
│
├── Provider Configuration
│
├── Raw Events
│
├── Canonical Events
│
├── Metrics
│
├── Analytics
│
├── Engineering Health
│
├── AI Insights
│
├── Audit Logs
│
└── System Configuration
```

Sensitive credentials should not be stored as plain text.

---

# 18. Background Processing

Long-running operations should be asynchronous.

Examples:

- Event ingestion
- Event transformation
- Analytics calculation
- Data synchronization
- AI insight generation
- Scheduled aggregation

Conceptual architecture:

```text
API
 ↓
Job Queue
 ↓
Worker
 ↓
Processing
 ↓
Database
```

A queue system may be introduced based on implementation requirements.

---

# 19. Caching

Caching can be used for:

- Frequently accessed dashboard metrics
- Configuration
- Provider metadata
- Expensive analytics results

Caching must never become the authoritative source of engineering data.

The database remains the source of truth.

---

# 20. Observability

CodeSense should provide:

### Logging

- Application logs
- Integration logs
- Processing logs
- Security logs
- AI gateway logs

### Metrics

- API latency
- Event processing rate
- Failed events
- Queue depth
- Database performance
- Provider synchronization status

### Health Checks

```text
/api/health
/api/health/database
/api/health/providers
/api/health/workers
```

---

# 21. Error Handling

The architecture must support:

```text
Validation Error
       ↓
Structured Error Response

Provider Failure
       ↓
Retry
       ↓
Dead Letter / Failure Queue

Processing Failure
       ↓
Retry
       ↓
Logging + Alert

AI Failure
       ↓
Return graceful fallback
       ↓
Core analytics continues
```

AI failures must never break core analytics.

---

# 22. Security Architecture

Security controls should exist at multiple layers.

```text
User
 ↓
Authentication
 ↓
Authorization
 ↓
API Validation
 ↓
Service Authorization
 ↓
Database Access Control
 ↓
Audit Logging
```

Security requirements include:

- Secure authentication
- RBAC
- Input validation
- Output validation
- Secrets management
- Encryption in transit
- Encryption at rest where appropriate
- Audit logging
- Least-privilege access
- Secure provider credentials

---

# 23. Deployment Architecture

CodeSense should be deployable using containers.

Conceptual deployment:

```text
                    ┌───────────────┐
                    │ Reverse Proxy │
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │ Frontend       │
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │ API / Backend  │
                    └───────┬───────┘
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ▼              ▼              ▼
        PostgreSQL      Worker/Queue     AI Gateway
```

The exact infrastructure can be finalized during implementation.

---

# 24. Recommended Technology Architecture

The initial implementation may use:

## Frontend

```text
React
TypeScript
Modern component library
Charting library
```

## Backend

```text
Python
FastAPI
Pydantic
SQLAlchemy
```

## Database

```text
PostgreSQL
```

## Background Processing

```text
Redis
Background workers / task queue
```

## AI

```text
AI Gateway
      ↓
Local LLM OR
Approved Cloud LLM
```

## Infrastructure

```text
Docker
Docker Compose
Nginx / Reverse Proxy
```

Technology choices may be revised during implementation if justified by a documented architectural decision.

---

# 25. Repository Architecture

Recommended structure:

```text
codesense/
│
├── frontend/
│   ├── src/
│   ├── components/
│   ├── pages/
│   ├── services/
│   └── tests/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── integrations/
│   │   ├── analytics/
│   │   ├── ai/
│   │   └── workers/
│   │
│   └── tests/
│
├── migrations/
│
├── docker/
│
├── scripts/
│
├── tests/
│
├── docs/
│
├── .env.example
├── docker-compose.yml
└── README.md
```

---

# 26. Dependency Rules

The architecture should enforce these dependency boundaries:

```text
Frontend
   ↓
API
   ↓
Application Services
   ↓
Domain / Analytics
   ↓
Repositories
   ↓
Database
```

Provider-specific integrations should not directly control the frontend.

```text
Provider
   ↓
Integration Adapter
   ↓
Canonical Model
   ↓
Analytics
   ↓
API
   ↓
Frontend
```

AI should remain isolated behind the AI Gateway.

```text
Analytics
   ↓
AI Gateway
   ↓
LLM
```

The rest of the application should not directly call an LLM provider.

---

# 27. Core Architectural Principles

The implementation must follow these principles.

### Principle 1 — Raw Data Preservation

Raw provider events remain untouched.

### Principle 2 — Canonical Analytics

Cross-provider analytics operate on the canonical analytical layer.

### Principle 3 — Privacy by Design

Developer identity must never reach the cloud LLM.

### Principle 4 — No Individual Productivity Scoring

CodeSense must not calculate or expose individual productivity scores.

### Principle 5 — Offline Capability

Core analytics must continue without Internet access.

### Principle 6 — AI Is Optional

Cloud AI failure must not break CodeSense core functionality.

### Principle 7 — Provider Independence

Analytics must not be tightly coupled to a specific provider.

### Principle 8 — Least Privilege

Users and services receive only the permissions required for their responsibilities.

### Principle 9 — API First

Frontend functionality should communicate through documented APIs.

### Principle 10 — Testability

Every major service must be independently testable.

---

# 28. Primary Data Flow

The canonical CodeSense flow is:

```text
External Engineering Platforms
             ↓
       Provider Adapters
             ↓
        Event Ingestion
             ↓
        Raw Event Store
             ↓
      Event Validation
             ↓
    Canonical Transformation
             ↓
     Canonical Data Layer
             ↓
       Analytics Engine
             ↓
 Engineering Health Calculation
             ↓
      ┌──────────┴──────────┐
      ↓                     ↓
 Dashboard              AI Gateway
                            ↓
                       AI Insights
```

---

# 29. Failure Isolation

Failures should be isolated between architectural components.

```text
Provider Failure
      ↓
Integration isolated
      ↓
Other providers continue
```

```text
AI Failure
      ↓
AI features unavailable
      ↓
Analytics continues
```

```text
Analytics Failure
      ↓
Processing retry
      ↓
Raw events remain available
```

```text
Database Failure
      ↓
Application enters degraded/unavailable state
      ↓
Recovery process
```

---

# 30. Scalability Strategy

The initial system can begin as a modular monolith.

Recommended evolution:

```text
Phase 1
Modular Monolith
       ↓
Phase 2
Background Workers
       ↓
Phase 3
Independent Processing Services
       ↓
Phase 4
Selective Service Separation
```

Do not introduce microservices solely for architectural complexity.

Service separation should occur only when justified by:

- Scale
- Performance
- Deployment independence
- Reliability
- Team ownership
- Security boundaries

---

# 31. Architecture Decision Requirements

Any change to this architecture must be documented in:

```text
docs/08-decisions/DECISIONS.md
```

Each architectural decision should contain:

```text
Decision
Status
Problem
Options considered
Selected option
Reason
Trade-offs
Impact
Date
```

---

# 32. Non-Negotiable Architecture Constraints

The following constraints are locked:

```text
1. Raw provider events must remain untouched.

2. A canonical analytical layer must exist for
   cross-provider analytics.

3. Developer identity must never be sent
   to the cloud LLM.

4. Individual productivity scores are prohibited.

5. Individual operational metrics may exist only
   where necessary and under appropriate
   privacy/access controls.

6. Core analytics must continue in offline mode.

7. Cloud AI features may become unavailable
   during offline operation.

8. Cloud AI must not be a dependency for
   core CodeSense functionality.

9. Provider integrations must use an
   abstraction/adapter model.

10. Architectural changes must be documented.
```

---

# 33. Definition of Architectural Completion

The architecture is considered implemented when:

- [ ] Frontend communicates with the backend through documented APIs.
- [ ] Authentication and authorization are implemented.
- [ ] Provider integrations use a common adapter pattern.
- [ ] Raw provider events are preserved.
- [ ] Canonical analytical models are implemented.
- [ ] Analytics operate on canonical data.
- [ ] Engineering Health Score is implemented.
- [ ] Individual productivity scoring is absent.
- [ ] AI requests pass through the AI Gateway.
- [ ] Developer identity is excluded from cloud AI requests.
- [ ] Core analytics operate without Internet connectivity.
- [ ] AI failure does not break core analytics.
- [ ] Database schema matches the approved architecture.
- [ ] Background processing supports retries and failure handling.
- [ ] Logging and health checks are implemented.
- [ ] Security controls are implemented.
- [ ] Architecture tests and acceptance tests pass.

---

# 34. Relationship With Other CodeSense Documents

This document connects to the remaining Vibe Coding Specification Pack:

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

`SYSTEM_ARCHITECTURE.md` should be treated as the **technical blueprint**.

It defines the boundaries and relationships between CodeSense components, while the other documents provide the detailed requirements needed to implement those components.