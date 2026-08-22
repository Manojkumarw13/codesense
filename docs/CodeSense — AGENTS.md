# CodeSense — AI Coding Agent Instructions

**Document Status:** Draft / Editable  
**Version:** 1.0  
**Project:** CodeSense  
**Purpose:** Instructions and constraints for AI coding agents working on the CodeSense codebase.

---

# 1. Agent Mission

You are an AI coding agent working on **CodeSense**, an engineering intelligence platform.

Your responsibility is to:

- Understand the existing architecture before coding.
- Implement requirements incrementally.
- Preserve existing functionality.
- Follow the approved architecture.
- Protect developer privacy.
- Maintain offline core functionality.
- Write maintainable and testable code.
- Run appropriate tests after changes.
- Never silently change locked requirements.

You are not authorized to redesign CodeSense architecture merely because another approach appears simpler.

---

# 2. Mandatory Documents to Read

Before making significant changes, read:

```text
docs/
│
├── PROJECT_CONTEXT.md
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

Priority order:

```text
PROJECT_CONTEXT
      ↓
PRD
      ↓
SYSTEM_ARCHITECTURE
      ↓
DATABASE_SCHEMA
      ↓
API_SPECIFICATION
      ↓
DATA_FLOW
      ↓
AI_DATA_BOUNDARY
      ↓
AGENTS
      ↓
TASKS
      ↓
ACCEPTANCE_TESTS
```

If documents conflict, stop and identify the conflict rather than guessing.

---

# 3. Core Operating Rule

Before changing code:

```text
Understand
    ↓
Inspect
    ↓
Plan
    ↓
Implement
    ↓
Test
    ↓
Review
    ↓
Document
```

Never:

```text
Guess
  ↓
Code
  ↓
Hope
```

---

# 4. Locked Architecture Rules

The following rules are mandatory.

## Rule 1 — Preserve Raw Events

Raw provider events must remain untouched.

```text
Provider Event
      ↓
Raw Event Store
      ↓
Immutable Payload
```

Do not rewrite raw provider payloads during normalization.

---

## Rule 2 — Use Canonical Data

Cross-provider analytics must operate on the canonical analytical layer.

Correct:

```text
GitHub
GitLab
   ↓
Canonical Events
   ↓
Analytics
```

Incorrect:

```text
Analytics
 ├── GitHub-specific logic
 └── GitLab-specific logic
```

---

## Rule 3 — No Individual Productivity Scores

Never implement:

```text
Developer
   ↓
Activity
   ↓
Productivity Score
```

Do not create:

```text
productivity_score
developer_score
employee_score
individual_productivity
```

or equivalent functionality.

Individual operational metrics may exist where legitimately required and protected by access controls.

---

## Rule 4 — Developer Identity Must Not Reach Cloud AI

Never send:

```text
developer_name
developer_id
user_id
email
employee_id
username
```

or equivalent identifying information to a cloud LLM.

Use anonymized or aggregated representations when AI needs context.

---

## Rule 5 — No Secrets to AI

Never send:

```text
API keys
Access tokens
Refresh tokens
Passwords
Private keys
Database credentials
Webhook secrets
JWT secrets
Authorization headers
```

to an AI provider.

---

## Rule 6 — No Raw Provider Payloads to Cloud AI

Never pass:

```text
raw_provider_events.payload
```

directly to a cloud LLM.

Use:

```text
Raw Data
   ↓
Canonical Data
   ↓
Analytics
   ↓
Sanitized AI Context
```

---

## Rule 7 — AI Gateway Is Mandatory

All AI communication must go through:

```text
AI Service
    ↓
Context Builder
    ↓
Privacy Filter
    ↓
AI Gateway
    ↓
LLM
```

No other service may directly call a cloud LLM.

---

## Rule 8 — AI Is Optional

Core CodeSense functionality must not depend on AI.

If AI is unavailable:

```text
Analytics           → Continue
Engineering Health  → Continue
Dashboard           → Continue
Data Processing     → Continue
Cloud AI Insights   → Unavailable
```

---

## Rule 9 — Offline Core Functionality

CodeSense must continue operating without Internet access.

Core offline functionality includes:

- Local data processing
- Canonical transformation
- Analytics
- Engineering Health calculation
- Dashboard access to locally available data

Cloud AI may become unavailable.

---

# 5. Technology Rules

Unless explicitly changed through an architectural decision, use:

## Backend

```text
Python
FastAPI
Pydantic
SQLAlchemy
Alembic
```

## Database

```text
PostgreSQL
```

## Frontend

```text
React
TypeScript
```

## Infrastructure

```text
Docker
Docker Compose
Nginx / Reverse Proxy
```

## Background Processing

```text
Redis
Worker / Task Queue
```

The exact queue implementation may be finalized during development.

---

# 6. Repository Structure

Maintain the following structure unless there is a documented reason to change it.

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
├── docker/
├── scripts/
├── tests/
├── docs/
│
├── .env.example
├── docker-compose.yml
└── README.md
```

Do not reorganize the repository merely for stylistic preference.

---

# 7. Backend Architecture Rules

Use layered architecture:

```text
API
 ↓
Application Service
 ↓
Domain Logic
 ↓
Repository
 ↓
Database
```

Do not put business logic directly inside API route handlers.

Bad:

```python
@app.get("/analytics")
def analytics():
    # 200 lines of business logic
```

Preferred:

```text
API Route
    ↓
Analytics Service
    ↓
Repository
    ↓
Database
```

---

# 8. Provider Integration Rules

Provider-specific logic must remain isolated.

Use:

```text
integrations/
├── base.py
├── github/
├── gitlab/
├── bitbucket/
└── jira/
```

Each provider should implement a common adapter interface.

Conceptually:

```python
class ProviderAdapter:
    authenticate()
    validate_connection()
    fetch_events()
    normalize_event()
    handle_webhook()
```

Do not place GitHub-specific logic inside the analytics engine.

---

# 9. Raw Event Rules

When receiving a provider event:

```text
Receive
  ↓
Validate
  ↓
Deduplicate
  ↓
Store Raw Event
  ↓
Queue Processing
```

The raw payload must be preserved.

Allowed updates:

```text
processing_status
processed_at
```

Do not modify:

```text
payload
provider_event_id
original event type
original received timestamp
```

---

# 10. Event Processing Rules

Event processing must be:

- Idempotent
- Retryable
- Observable
- Fault tolerant

Processing:

```text
Raw Event
   ↓
Worker
   ↓
Classification
   ↓
Validation
   ↓
Canonical Transformation
   ↓
Canonical Event
```

If processing fails:

```text
Raw Event
   ↓
Retry
   ↓
Failure
```

Never delete the raw event because processing failed.

---

# 11. Idempotency Rules

Provider events must be deduplicated using:

```text
provider_connection_id
+
provider_event_id
```

Repeated delivery of the same provider event must not create duplicate canonical events.

Operations that may be retried should support idempotency keys where appropriate.

---

# 12. Database Rules

Use SQLAlchemy for database access.

Use Alembic for schema migrations.

Never manually modify production schema without a migration.

Correct:

```text
Model Change
    ↓
Alembic Migration
    ↓
Migration Test
    ↓
Apply
```

Every database change must consider:

- Existing data
- Foreign keys
- Indexes
- Constraints
- Backward compatibility
- Migration rollback/recovery

---

# 13. Database Source of Truth

PostgreSQL is the authoritative source for:

```text
Users
Organizations
Projects
Repositories
Raw Events
Canonical Events
Metrics
Engineering Health
AI Insights
Audit Logs
Configuration
```

Do not make:

```text
Redis
Frontend state
AI output
Cache
Temporary files
```

the source of truth.

---

# 14. API Rules

All APIs use:

```text
/api/v1/
```

API routes must:

- Validate input
- Authenticate requests
- Authorize access
- Return structured responses
- Handle errors consistently
- Avoid leaking secrets
- Respect organization boundaries

Frontend must never access PostgreSQL directly.

---

# 15. Authorization Rules

Every protected operation must verify:

```text
Authentication
      ↓
Organization Membership
      ↓
Role Permission
      ↓
Resource Permission
```

Never trust frontend authorization.

This is invalid:

```text
if user.is_admin:
    # frontend says user is admin
```

Authorization must be enforced server-side.

---

# 16. Multi-Tenant Isolation

Organization data must remain isolated.

Every organization-owned query must apply appropriate organization scoping.

Never assume that:

```text
project_id
```

alone is sufficient to authorize access.

Validate the relationship:

```text
User
 ↓
Organization
 ↓
Project
 ↓
Resource
```

---

# 17. API Error Handling

Use consistent errors.

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

Do not expose:

```text
Stack traces
Database credentials
SQL queries
Internal secrets
Provider tokens
```

in production API responses.

---

# 18. Frontend Rules

Frontend responsibilities:

- UI rendering
- User interaction
- Client-side validation
- API communication
- State management

Frontend must not contain:

- Database credentials
- Provider credentials
- AI provider keys
- Security-sensitive business logic

---

# 19. Analytics Rules

Analytics must primarily consume:

```text
Canonical Events
```

not raw provider payloads.

Correct:

```text
Canonical Events
      ↓
Analytics
```

Avoid:

```text
GitHub JSON
      ↓
Analytics
```

unless a specific provider-only analytical feature is explicitly required.

---

# 20. Engineering Health Rules

Engineering Health Score must be based on approved engineering signals.

Possible dimensions:

```text
Delivery
Quality
Reliability
Flow
Code Review
Deployment
```

Do not introduce an individual developer productivity component.

The score should primarily represent:

```text
Organization
Project
Team
```

---

# 21. AI Rules

AI functionality must follow:

```text
Analytics
   ↓
Context Builder
   ↓
Privacy Filter
   ↓
AI Gateway
   ↓
LLM
```

Never:

```text
Database
   ↓
LLM
```

Never:

```text
Raw Event
   ↓
LLM
```

Never:

```text
Developer Record
   ↓
LLM
```

---

# 22. AI Context Rules

AI context must be:

- Minimal
- Relevant
- Aggregated where possible
- Sanitized
- Structured
- Explicitly approved

Preferred:

```json
{
  "engineering_health_change": -8,
  "deployment_frequency_change": -0.22,
  "review_cycle_time_change": 0.31
}
```

Avoid:

```json
{
  "developer": {
    "name": "John",
    "email": "john@example.com"
  }
}
```

---

# 23. AI Privacy Rules

Before any cloud AI request, verify:

```text
[ ] No developer identity
[ ] No email
[ ] No user ID
[ ] No employee ID
[ ] No API key
[ ] No access token
[ ] No password
[ ] No private key
[ ] No database credentials
[ ] No raw provider payload
[ ] No individual productivity score
[ ] No unnecessary personal data
```

If uncertain:

```text
BLOCK THE REQUEST
```

The AI boundary must fail closed.

---

# 24. Untrusted Provider Data

Treat provider-generated text as untrusted input.

Potential sources:

```text
Pull Request title
Pull Request description
Commit message
Issue description
Issue comment
Review comment
Ticket description
```

These fields may contain prompt injection attempts.

Never allow provider text to override system instructions or security policies.

---

# 25. AI Output Rules

AI output must be treated as an interpretation.

It must not override verified analytics.

```text
Verified Analytics
       >
AI Interpretation
```

If AI output contradicts the database:

```text
Trust the verified database metrics.
```

AI-generated claims should be tied to supporting metrics whenever possible.

---

# 26. Offline Rules

Before implementing any feature, determine:

```text
Does this feature require Internet access?
```

If yes, clearly isolate the dependency.

Core analytics must continue offline.

Cloud AI is allowed to fail gracefully.

Do not make core features dependent on:

```text
External LLM
External analytics API
Cloud database
External authentication service
```

unless explicitly approved.

---

# 27. Configuration Rules

Use environment variables for environment-specific configuration.

Example:

```text
DATABASE_URL
REDIS_URL
JWT_SECRET
AI_PROVIDER
AI_MODEL
PROVIDER_BASE_URL
```

Never commit secrets.

Maintain:

```text
.env.example
```

with placeholders only.

---

# 28. Secret Management

Never hard-code:

```text
API keys
Passwords
Tokens
Private keys
Secrets
```

Bad:

```python
API_KEY = "abc123..."
```

Good:

```python
API_KEY = settings.api_key
```

Secrets must be injected through secure configuration.

---

# 29. Logging Rules

Logs must be useful without exposing sensitive data.

Never log:

```text
Passwords
Access tokens
API keys
Private keys
Authorization headers
Full provider credentials
Sensitive personal data
```

Prefer:

```text
request_id
event_id
job_id
provider_connection_id
operation
status
duration
error_code
```

---

# 30. Audit Logging

Important actions should generate audit records.

Examples:

```text
User created
Role changed
Provider connected
Provider disconnected
Configuration changed
Project created
Permission changed
AI insight generated
Sensitive resource accessed
```

Audit logs should be append-only wherever practical.

---

# 31. Testing Requirements

Every implementation must include appropriate tests.

Minimum:

```text
Unit Tests
Integration Tests
API Tests
Security Tests
Privacy Tests
```

For significant workflows:

```text
End-to-End Tests
```

Do not mark a task complete only because the code compiles.

---

# 32. Privacy Testing

Any AI-related change must test:

```text
Developer identity filtering
Secret detection
Raw payload blocking
PII filtering
Prompt injection handling
Fail-closed behavior
```

Example:

```text
Input:
developer_email = "test@example.com"

Expected:
NOT PRESENT IN CLOUD AI REQUEST
```

---

# 33. Offline Testing

Offline-sensitive functionality must be tested with network access disabled.

Verify:

```text
[ ] Event processing works
[ ] Canonical transformation works
[ ] Analytics work
[ ] Engineering Health works
[ ] Dashboard works
[ ] Cloud AI fails gracefully
```

---

# 34. Definition of Done

A coding task is complete only when:

```text
[ ] Requirement understood
[ ] Existing implementation inspected
[ ] Code implemented
[ ] Tests added/updated
[ ] Tests pass
[ ] Security checked
[ ] Privacy checked
[ ] Offline behavior considered
[ ] Documentation updated if necessary
[ ] No locked requirement violated
```

---

# 35. Task Execution Workflow

For every task:

```text
1. Read TASKS.md
        ↓
2. Identify current task
        ↓
3. Read relevant requirements
        ↓
4. Inspect existing code
        ↓
5. Identify affected modules
        ↓
6. Create implementation plan
        ↓
7. Implement smallest correct change
        ↓
8. Run tests
        ↓
9. Fix failures
        ↓
10. Review architecture constraints
        ↓
11. Update documentation
        ↓
12. Mark task complete
```

---

# 36. Do Not Over-Engineer

Prefer the simplest architecture that satisfies the requirements.

Do not introduce:

```text
Microservices
Complex event buses
Additional databases
Multiple caches
Additional AI agents
Unnecessary abstractions
```

without a documented reason.

The initial implementation should prefer a modular monolith unless scale or reliability requires separation.

---

# 37. Change Scope

When implementing a task:

```text
Understand requested change
        ↓
Identify required files
        ↓
Modify only necessary components
```

Avoid unrelated refactoring.

Do not rewrite working modules merely because you prefer a different coding style.

---

# 38. Backward Compatibility

Before modifying an existing API, database schema, or data model, check:

```text
Frontend dependencies
API clients
Database migrations
Existing tests
Provider integrations
Background workers
```

Avoid breaking existing functionality.

---

# 39. Dependency Management

Before adding a dependency:

Ask:

```text
1. Is it actually required?
2. Is an existing dependency sufficient?
3. Is it actively maintained?
4. Does it introduce security risk?
5. Does it increase deployment complexity?
6. Does it work offline?
```

Do not add packages for trivial functionality.

---

# 40. Code Quality Rules

Code should be:

- Readable
- Modular
- Testable
- Typed where appropriate
- Small in scope
- Explicit
- Consistent

Avoid:

```text
Huge functions
Hidden global state
Duplicated business logic
Hard-coded configuration
Dead code
Unused dependencies
```

---

# 41. Python Rules

Use:

```text
Type hints
Pydantic models
Clear service boundaries
Repository pattern where appropriate
Structured exceptions
```

Prefer:

```python
def get_project(project_id: UUID) -> Project:
```

over untyped interfaces when typing improves correctness.

---

# 42. FastAPI Rules

Routes should remain thin.

Preferred:

```text
Router
 ↓
Service
 ↓
Repository
```

Do not place complex database queries and business calculations directly inside route handlers.

Use Pydantic request/response schemas.

---

# 43. SQLAlchemy Rules

Use SQLAlchemy models for persistence.

Avoid raw SQL unless:

- Performance requires it
- PostgreSQL-specific functionality is required
- The query is reviewed and tested

All raw SQL must use parameterization.

Never construct SQL using string concatenation with user input.

---

# 44. Migration Rules

Every schema change requires:

```text
Model Update
     ↓
Migration
     ↓
Migration Test
     ↓
Application Test
```

Check both:

```text
Upgrade
Downgrade
```

where downgrade is supported by the migration strategy.

---

# 45. API Documentation Rules

When adding or modifying an endpoint:

Update:

```text
API specification
OpenAPI schema
Request model
Response model
Tests
```

The API specification must remain synchronized with the implementation.

---

# 46. Data Flow Rules

Any new data source must follow:

```text
Provider
 ↓
Adapter
 ↓
Raw Event
 ↓
Canonical Event
 ↓
Analytics
```

Do not bypass the raw-event layer unless the requirement explicitly defines a non-event configuration resource.

---

# 47. New Provider Checklist

Before adding a provider:

```text
[ ] Provider adapter created
[ ] Authentication implemented
[ ] Connection validation implemented
[ ] Webhook/polling support defined
[ ] Provider event mapping defined
[ ] Raw event ingestion implemented
[ ] Deduplication implemented
[ ] Canonical transformation implemented
[ ] Retry behavior implemented
[ ] Error handling implemented
[ ] Tests added
[ ] Security reviewed
[ ] Documentation updated
```

---

# 48. New AI Feature Checklist

Before implementing an AI feature:

```text
[ ] Define exact AI purpose
[ ] Identify required data
[ ] Minimize data
[ ] Classify data
[ ] Remove developer identity
[ ] Remove secrets
[ ] Remove raw provider payloads
[ ] Implement privacy filtering
[ ] Implement AI Gateway integration
[ ] Validate AI output
[ ] Add privacy tests
[ ] Add failure handling
[ ] Verify offline behavior
[ ] Update AI_DATA_BOUNDARY.md
```

---

# 49. New Database Table Checklist

Before adding a table:

```text
[ ] Why is the table required?
[ ] Which requirement does it support?
[ ] Does it duplicate existing data?
[ ] Does it need organization_id?
[ ] What are its foreign keys?
[ ] What indexes are required?
[ ] What retention policy applies?
[ ] Does it contain personal data?
[ ] Does it contain secrets?
[ ] Does it affect AI privacy?
[ ] Is a migration required?
[ ] Are tests required?
```

---

# 50. New API Endpoint Checklist

```text
[ ] Requirement exists
[ ] Authorization defined
[ ] Request schema defined
[ ] Response schema defined
[ ] Error responses defined
[ ] Pagination considered
[ ] Rate limiting considered
[ ] Audit logging considered
[ ] Tests added
[ ] OpenAPI updated
[ ] API_SPECIFICATION.md updated
```

---

# 51. Security Review Trigger

Perform additional security review when changing:

```text
Authentication
Authorization
Provider credentials
Webhooks
AI Gateway
Privacy filtering
Database permissions
File uploads
Exports
Audit logs
Network configuration
```

---

# 52. Privacy Review Trigger

Perform additional privacy review when changing:

```text
User data
Developer identity
Individual metrics
Analytics
AI context
AI prompts
AI responses
Data exports
Logging
Data retention
```

---

# 53. Architecture Change Trigger

Stop and request architectural review if a change introduces:

```text
New database
New external service
New AI provider
New major framework
New microservice
New data source
New identity system
New analytics methodology
New individual-level scoring
New cloud dependency
```

Do not silently introduce these changes.

---

# 54. Conflict Resolution

If two documents conflict:

```text
DO NOT GUESS
```

Follow:

```text
Identify conflict
      ↓
Document conflict
      ↓
Check locked decisions
      ↓
Check latest approved requirement
      ↓
Request clarification if needed
```

Never choose an implementation merely because it is easier.

---

# 55. Locked Requirement Protection

The agent must treat these as locked:

```text
Raw provider events remain untouched.

Canonical analytical layer exists.

Developer identity never reaches cloud LLM.

Individual productivity scores are prohibited.

Core analytics work offline.

Cloud AI may become unavailable offline.

AI is not required for core analytics.
```

Do not weaken or reinterpret these requirements.

---

# 56. Git Rules

Use meaningful commits.

Example:

```text
feat: add GitHub provider adapter
feat: implement canonical pull request events
fix: prevent duplicate webhook processing
test: add AI privacy boundary tests
docs: update API specification
```

Avoid:

```text
update
changes
stuff
fix
test
```

unless the repository's existing convention requires otherwise.

---

# 57. Commit Scope

A commit should preferably represent one logical change.

Good:

```text
feat: implement provider event ingestion
```

Avoid mixing:

```text
Provider ingestion
+
Frontend redesign
+
Database migration
+
Unrelated refactoring
```

in one commit.

---

# 58. Before Committing

Run appropriate:

```text
Lint
Type checks
Unit tests
Integration tests
Security tests
Privacy tests
```

At minimum, verify that the affected functionality works.

---

# 59. Agent Self-Review

Before declaring a task complete, ask:

```text
1. Did I implement the actual requirement?
2. Did I inspect existing code first?
3. Did I introduce unnecessary complexity?
4. Did I break an existing API?
5. Did I modify raw provider data?
6. Did I bypass canonical data?
7. Did I introduce individual productivity scoring?
8. Could developer identity reach cloud AI?
9. Could secrets reach AI?
10. Does the feature work offline where required?
11. Did I add tests?
12. Did I update relevant documentation?
```

If any answer indicates a violation, fix it before completion.

---

# 60. Final Agent Workflow

The standard CodeSense vibe-coding loop is:

```text
                    ┌───────────────┐
                    │ Read Task     │
                    └───────┬───────┘
                            ↓
                    ┌───────────────┐
                    │ Read Docs     │
                    └───────┬───────┘
                            ↓
                    ┌───────────────┐
                    │ Inspect Code  │
                    └───────┬───────┘
                            ↓
                    ┌───────────────┐
                    │ Plan Change   │
                    └───────┬───────┘
                            ↓
                    ┌───────────────┐
                    │ Implement     │
                    └───────┬───────┘
                            ↓
                    ┌───────────────┐
                    │ Run Tests     │
                    └───────┬───────┘
                            ↓
                    ┌───────────────┐
                    │ Security      │
                    │ Privacy Check │
                    └───────┬───────┘
                            ↓
                    ┌───────────────┐
                    │ Review        │
                    └───────┬───────┘
                            ↓
                    ┌───────────────┐
                    │ Document      │
                    └───────┬───────┘
                            ↓
                    ┌───────────────┐
                    │ Complete Task │
                    └───────────────┘
```

---

# 61. Agent Completion Criteria

The agent must not report:

```text
"Done"
```

until it has verified:

```text
[ ] Implementation completed
[ ] Tests executed
[ ] Tests pass or known failures reported
[ ] Security requirements checked
[ ] Privacy requirements checked
[ ] Offline requirements checked
[ ] Architecture constraints checked
[ ] Documentation updated where necessary
```

If something cannot be verified, explicitly state it.

---

# 62. Non-Negotiable Rules Summary

```text
┌─────────────────────────────────────────────┐
│              CODESENSE RULES                │
├─────────────────────────────────────────────┤
│                                             │
│ 1. Preserve raw provider events.            │
│                                             │
│ 2. Use canonical data for analytics.        │
│                                             │
│ 3. Never create individual productivity     │
│    scores.                                  │
│                                             │
│ 4. Never send developer identity to cloud   │
│    LLMs.                                    │
│                                             │
│ 5. Never send secrets to AI.                │
│                                             │
│ 6. Never send raw provider payloads to      │
│    cloud AI.                                │
│                                             │
│ 7. All AI communication goes through the    │
│    AI Gateway.                              │
│                                             │
│ 8. AI is optional for core functionality.   │
│                                             │
│ 9. Core analytics must work offline.        │
│                                             │
│ 10. Do not silently change locked          │
│     requirements.                           │
│                                             │
└─────────────────────────────────────────────┘
```

---

# 63. Relationship With Other Documents

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

`AGENTS.md` is the **operational instruction manual for the AI coding agent**.

It converts the CodeSense architecture and locked requirements into concrete rules that must be followed during implementation.

Any future change to a locked requirement should be reflected here before the coding agent is allowed to implement it.