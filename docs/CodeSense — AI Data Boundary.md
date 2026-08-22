# CodeSense — AI Data Boundary

**Document Status:** Draft / Editable  
**Version:** 1.0  
**Project:** CodeSense  
**Purpose:** Define the security, privacy, and data-governance boundary between CodeSense and AI/LLM systems.

---

# 1. Purpose

The AI Data Boundary defines:

- What data AI can access
- What data AI cannot access
- What data may be sent to cloud LLMs
- What data must remain inside CodeSense
- How data is sanitized
- How AI requests are constructed
- How AI responses are validated
- How offline AI behaves
- How developer privacy is protected

The fundamental principle is:

```text
CodeSense Data
      ↓
Analytics
      ↓
Privacy / AI Boundary
      ↓
Approved AI Context
      ↓
LLM
```

AI must never bypass the boundary.

---

# 2. Core Privacy Principle

The most important CodeSense rule is:

> **Developer identity must never be sent to a cloud LLM.**

This is a locked architectural requirement.

The AI system may use engineering information necessary to generate useful insights, but it must not receive identifying information about individual developers.

---

# 3. AI Architecture

```text
┌─────────────────────────────┐
│       CodeSense Core        │
│                             │
│ Raw Events                  │
│ Canonical Events            │
│ Analytics                   │
│ Engineering Health          │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│      AI Context Builder     │
│                             │
│ Select approved data        │
│ Aggregate                   │
│ Anonymize                   │
│ Remove sensitive fields     │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│       AI Privacy Filter     │
│                             │
│ Identity removal            │
│ Secret detection            │
│ Credential detection        │
│ PII filtering               │
│ Raw payload blocking        │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│         AI Gateway          │
│                             │
│ Policy enforcement          │
│ Provider selection          │
│ Request logging             │
│ Response validation         │
└──────────────┬──────────────┘
               │
          ┌────┴────┐
          ▼         ▼
     Local LLM   Cloud LLM
```

---

# 4. Trust Zones

CodeSense should be divided into trust zones.

```text
ZONE 1 — INTERNAL DATA
──────────────────────
Raw Provider Data
User Identity
Credentials
Secrets
Audit Data


ZONE 2 — ANALYTICAL DATA
─────────────────────────
Canonical Events
Aggregated Metrics
Engineering Health
Trends


ZONE 3 — AI-SAFE DATA
──────────────────────
Sanitized Metrics
Anonymized Trends
Aggregated Engineering Information
Approved Context


ZONE 4 — EXTERNAL AI
────────────────────
Cloud LLM
External AI Provider
```

The boundary between Zone 3 and Zone 4 is the strictest external data boundary.

---

# 5. Data Classification

Every data category should have a classification.

| Classification | Description | Cloud AI |
|---|---|---|
| PUBLIC | Non-sensitive information | Allowed |
| INTERNAL | CodeSense internal information | Restricted |
| SENSITIVE | Information that could expose users/projects | Restricted |
| PERSONAL | Information identifying people | Prohibited |
| SECRET | Credentials, tokens, keys | Prohibited |
| RAW_PROVIDER_DATA | Original external payload | Prohibited |
| AI_SAFE | Explicitly approved sanitized data | Allowed |

---

# 6. Data Classification Examples

## PUBLIC

Examples:

```text
Public technology names
Generic engineering concepts
Public documentation
Generic metric definitions
```

Cloud AI:

```text
ALLOWED
```

---

## INTERNAL

Examples:

```text
Internal project names
Internal architecture metadata
Internal configuration
```

Cloud AI:

```text
DEFAULT: NOT ALLOWED
```

Only explicitly approved fields may be exposed.

---

## SENSITIVE

Examples:

```text
Internal repository information
Internal incident information
Detailed project information
Non-public engineering information
```

Cloud AI:

```text
NOT ALLOWED BY DEFAULT
```

Only sanitized, aggregated derivatives may be allowed.

---

## PERSONAL

Examples:

```text
Developer name
Developer email
User ID
Employee ID
Personal profile
Personal contact information
```

Cloud AI:

```text
PROHIBITED
```

---

## SECRET

Examples:

```text
API keys
OAuth tokens
Access tokens
Passwords
Database credentials
Webhook secrets
Private keys
JWT secrets
```

Cloud AI:

```text
ABSOLUTELY PROHIBITED
```

---

# 7. Raw Provider Data Boundary

Raw provider events must remain inside CodeSense.

```text
Raw Provider Event
       │
       X
       │
       ▼
Cloud LLM
```

This is prohibited.

Correct:

```text
Raw Provider Event
       ↓
CodeSense Processing
       ↓
Canonical Data
       ↓
Analytics
       ↓
Sanitized Context
       ↓
AI
```

---

# 8. Developer Identity Boundary

Developer identity may exist internally when required for legitimate application functionality.

Example:

```text
Internal Database

user_id = "internal-123"
display_name = "Developer Name"
email = "developer@example.com"
```

AI context:

```text
actor = "anonymous-actor-A"
```

The mapping must remain inside CodeSense.

The AI provider must not receive the mapping.

---

# 9. Identity Fields That Must Never Reach Cloud AI

The following fields are prohibited:

```text
user_id
developer_id
employee_id
email
display_name
first_name
last_name
username
login
avatar_url
personal_url
profile_url
phone_number
```

Equivalent provider-specific identity fields are also prohibited.

---

# 10. Credential Fields That Must Never Reach AI

The following are prohibited:

```text
access_token
refresh_token
api_key
client_secret
client_id
password
private_key
secret
webhook_secret
database_password
jwt_secret
authorization_header
cookie
session_token
```

Any provider-specific equivalent must also be blocked.

---

# 11. Raw Payload Blocking

AI requests must not include:

```text
raw_provider_events.payload
```

or equivalent raw payload structures.

Instead:

```text
Raw Payload
     ↓
Extract Approved Fields
     ↓
Normalize
     ↓
Aggregate
     ↓
Sanitize
     ↓
AI Context
```

---

# 12. AI-Safe Data

The following information may be considered AI-safe after appropriate validation:

```text
Aggregated engineering metrics
Engineering Health Score
Team-level trends
Project-level trends
Time-series summaries
Anonymized event statistics
Metric changes
System-level engineering patterns
```

Example:

```text
Review cycle time increased by 18%.
Deployment frequency decreased by 12%.
Engineering Health Score decreased from 84 to 78.
```

This is preferable to exposing individual event records.

---

# 13. AI-Safe Context Example

### Internal Data

```json
{
  "team_id": "team-123",
  "team_name": "Platform Engineering",
  "developer_count": 8,
  "review_cycle_time": 6.2,
  "deployment_frequency": 4.8
}
```

### AI-Safe Context

```json
{
  "scope": "engineering_team",
  "team_alias": "Team A",
  "review_cycle_time_hours": 6.2,
  "deployment_frequency_per_week": 4.8,
  "trend": "review_cycle_time_increasing"
}
```

The identity mapping stays internal.

---

# 14. Aggregation Requirement

Where practical, AI should receive aggregated information rather than raw individual events.

Preferred:

```text
Team-level metrics
Project-level metrics
Organization-level metrics
```

Avoid:

```text
Individual event sequences
Individual activity timelines
Individual developer comparisons
```

The purpose is to provide engineering intelligence rather than employee surveillance.

---

# 15. Individual Metrics

CodeSense may retain individual operational metrics where necessary.

Examples:

```text
Review participation
PR ownership
Event attribution
Operational activity
```

However, these metrics must be protected by access controls and must not automatically become AI input.

---

# 16. Individual Productivity Prohibition

The following is prohibited:

```text
Individual Activity
       ↓
Weighted Formula
       ↓
Individual Productivity Score
       ↓
AI
```

Also prohibited:

```text
Developer A = 82 productivity
Developer B = 64 productivity
```

CodeSense must not calculate, store, expose, or send individual productivity scores to AI.

---

# 17. Team-Level Engineering Health

The preferred flow is:

```text
Engineering Events
       ↓
Canonical Data
       ↓
Aggregated Metrics
       ↓
Team Engineering Health
       ↓
AI Context
```

Example:

```text
Team Health = 82
Review Cycle = 5.4 hours
Deployment Frequency = 9/week
Change Failure Rate = 6%
```

This can be used to generate engineering-level insights.

---

# 18. AI Context Builder

The AI Context Builder is responsible for constructing AI requests.

Responsibilities:

1. Select approved data.
2. Remove unnecessary fields.
3. Aggregate data.
4. Anonymize identities.
5. Detect sensitive information.
6. Detect secrets.
7. Apply policy rules.
8. Produce structured AI context.

Flow:

```text
Analytics
   ↓
Context Builder
   ↓
Field Selection
   ↓
Aggregation
   ↓
Anonymization
   ↓
Privacy Filter
   ↓
AI Gateway
```

---

# 19. AI Privacy Filter

The Privacy Filter is a mandatory security component.

It should inspect:

```text
Request metadata
Prompt
Structured context
JSON fields
Nested objects
Strings
URLs
Headers
Provider metadata
```

It must detect:

```text
Identity
PII
Credentials
Secrets
Raw payloads
Restricted data
```

---

# 20. Secret Detection

The AI boundary should use multiple detection strategies.

### Field-based detection

Block fields such as:

```text
token
secret
password
api_key
authorization
private_key
```

### Pattern detection

Detect patterns resembling:

```text
JWT
API keys
OAuth tokens
Private keys
Connection strings
Passwords
```

### Content inspection

Scan strings and nested JSON objects.

---

# 21. Fail-Closed Behavior

If the AI privacy filter cannot determine whether data is safe:

```text
Unknown Data
     ↓
BLOCK
```

Do not assume unknown data is safe.

The default should be:

```text
Allow only explicitly approved data.
```

---

# 22. AI Gateway

The AI Gateway is the only component allowed to communicate with external LLM providers.

```text
Application
    ↓
AI Service
    ↓
AI Context Builder
    ↓
Privacy Filter
    ↓
AI Gateway
    ↓
LLM Provider
```

No other backend service should directly call a cloud LLM.

---

# 23. AI Gateway Responsibilities

The AI Gateway handles:

- Provider selection
- Authentication
- Request validation
- Privacy enforcement
- Model selection
- Timeout handling
- Retry policy
- Response validation
- Usage tracking
- Error handling
- Audit logging

---

# 24. Cloud AI Boundary

Cloud AI should only receive:

```text
Approved AI-safe context
+
Required prompt
+
Non-sensitive configuration
```

It must not receive:

```text
Raw provider payloads
Developer identity
Credentials
Secrets
Access tokens
Personal information
Database credentials
```

---

# 25. Local LLM Boundary

A local LLM operates inside the trusted CodeSense environment.

```text
CodeSense
   ↓
AI Context
   ↓
Local LLM
```

Strict privacy rules apply uniformly to both cloud and local LLMs. Developer identities, personal data, and raw event details must be strictly stripped from all contexts sent to any LLM.

---

# 26. Cloud vs Local AI Data Access

| Data Type | Local LLM | Cloud LLM |
|---|---:|---:|
| Aggregated metrics | Allowed | Allowed |
| Engineering Health | Allowed | Allowed |
| Team trends | Allowed after sanitization | Allowed after sanitization |
| Project trends | Allowed after sanitization | Allowed after sanitization |
| Developer identity | Prohibited | Prohibited |
| Personal information | Prohibited | Prohibited |
| Raw provider events | Prohibited | Prohibited |
| Credentials | Prohibited | Prohibited |
| Secrets | Prohibited | Prohibited |
| API keys | Prohibited | Prohibited |

---

# 27. AI Request Lifecycle

```text
1. User requests insight
             ↓
2. API validates authorization
             ↓
3. Analytics data selected
             ↓
4. Context Builder creates context
             ↓
5. Identity removed
             ↓
6. Secrets removed
             ↓
7. Raw data removed
             ↓
8. Privacy validation
             ↓
9. AI Gateway
             ↓
10. LLM
             ↓
11. Response validation
             ↓
12. Insight stored
             ↓
13. Dashboard
```

---

# 28. AI Request Example

User request:

```text
"Why did engineering health decline this month?"
```

Internal analytics:

```text
Engineering Health:
84 → 76

Review Cycle:
4.2h → 6.1h

Deployment Frequency:
10/week → 7/week

Change Failure Rate:
4% → 8%
```

AI-safe context:

```json
{
  "period": "monthly",
  "engineering_health_change": -8,
  "review_cycle_time_change_percent": 45,
  "deployment_frequency_change_percent": -30,
  "change_failure_rate_change_percent": 100
}
```

AI receives the sanitized context.

---

# 29. AI Response Validation

AI output must be validated before being shown to users.

Validation should check:

- Schema
- Required fields
- Length limits
- Unsafe content
- Unsupported claims
- Data leakage
- Unexpected identity references
- Secrets
- Prompt injection artifacts

---

# 30. AI Output Must Not Become Source of Truth

AI-generated insights are interpretations.

```text
Analytics Database
       ↓
SOURCE OF TRUTH

AI Insight
       ↓
INTERPRETATION
```

If an AI statement conflicts with verified analytics:

```text
Verified Analytics > AI Output
```

---

# 31. AI Hallucination Control

AI output should reference the analytical context from which it was generated.

Example:

```json
{
  "insight": "Review cycle time increased.",
  "supporting_metrics": [
    "review_cycle_time",
    "engineering_health"
  ]
}
```

The AI must not invent metrics that were not provided.

---

# 32. Prompt Injection Protection

Provider data may contain user-controlled text.

Examples:

```text
Pull Request title
Commit message
Issue description
Comment
Ticket description
```

These fields must be treated as **untrusted input**.

A malicious provider payload must not be allowed to manipulate the system prompt or AI policy.

---

# 33. Prompt Injection Boundary

```text
Provider Text
     ↓
UNTRUSTED DATA
     ↓
Sanitization
     ↓
Structured Context
     ↓
System Instructions
     ↓
LLM
```

Provider content must never be treated as system instructions.

---

# 34. AI Prompt Structure

Recommended conceptual structure:

```text
SYSTEM POLICY
     ↓
AI ROLE
     ↓
TASK
     ↓
APPROVED ANALYTICAL CONTEXT
     ↓
OUTPUT FORMAT
```

Untrusted provider text should be explicitly marked as data.

---

# 35. Data Minimization

AI requests should follow:

> Send the minimum data necessary to answer the question.

Example:

If the user asks:

```text
"Why did deployment reliability decline?"
```

Do not send:

```text
Developer profiles
Full repository data
Complete commit history
Raw provider payloads
```

Send:

```text
Deployment success rate
Failure rate
Change failure rate
Relevant time periods
Aggregated engineering trends
```

---

# 36. AI Data Retention

AI requests and responses should have configurable retention policies.

Possible data:

```text
AI request metadata
Sanitized context
Model/provider
AI response
Generated insight
```

Sensitive raw data must not be stored merely because it was used internally to construct an AI request.

---

# 37. AI Audit Trail

Each AI request should be traceable.

```text
AI Request
    ↓
Request ID
    ↓
User / System Actor
    ↓
Project Scope
    ↓
AI Provider
    ↓
Model
    ↓
Sanitized Context
    ↓
Response
```

The audit record must not expose secrets.

---

# 38. AI Access Control

Not every user should necessarily be able to generate or view every AI insight.

Authorization should consider:

```text
User Role
Organization
Project
Team
Insight Type
Data Sensitivity
```

Example:

```text
Developer
   ↓
Own permitted project insights

Manager
   ↓
Team/project insights

Admin
   ↓
Organization-level insights
```

Exact permissions should be defined in the authorization model.

---

# 39. Offline AI Behavior

When Internet connectivity is unavailable:

```text
Cloud AI
   ↓
UNAVAILABLE
```

Core functionality remains:

```text
Raw Data
   ↓
Canonical Data
   ↓
Analytics
   ↓
Engineering Health
   ↓
Dashboard
```

If a local LLM is configured:

```text
Analytics
   ↓
AI Gateway
   ↓
Local LLM
```

may continue.

---

# 40. Cloud AI Failure

If the cloud AI provider fails:

```text
AI Gateway
     ↓
Provider Failure
     ↓
Retry / Fallback
     ↓
AI unavailable
```

The application must gracefully display:

```text
AI insights currently unavailable.
Core engineering analytics remain available.
```

---

# 41. Data Flow Summary

The secure AI data flow is:

```text
                    CODE SENSE INTERNAL
────────────────────────────────────────────────────

Raw Provider Events
        ↓
Canonical Events
        ↓
Analytics
        ↓
Engineering Health
        ↓
AI Context Builder
        ↓
Aggregation
        ↓
Anonymization
        ↓
Secret Detection
        ↓
Privacy Filter
        ↓
────────────────── AI BOUNDARY ──────────────────
        ↓
AI Gateway
        ↓
Local / Cloud LLM
        ↓
Response Validation
        ↓
AI Insight
        ↓
CodeSense Dashboard
```

---

# 42. Prohibited Data Flow

The following flows must never exist:

```text
Raw Provider Event
       ↓
Cloud LLM
```

```text
Developer Identity
       ↓
Cloud LLM
```

```text
Database
       ↓
Cloud LLM
```

```text
Provider Credentials
       ↓
Cloud LLM
```

```text
API Keys
       ↓
Cloud LLM
```

```text
Individual Productivity Score
       ↓
Cloud LLM
```

---

# 43. Security Controls

The AI boundary should implement:

- Allowlist-based data selection
- Field-level filtering
- PII detection
- Secret detection
- Raw payload blocking
- Identity anonymization
- Prompt injection protection
- Input validation
- Output validation
- Access control
- Audit logging
- Rate limiting
- Timeout controls
- Fail-closed behavior

---

# 44. Recommended AI Gateway Modules

```text
ai/
│
├── gateway/
│   ├── provider_manager.py
│   ├── request_validator.py
│   ├── response_validator.py
│   └── router.py
│
├── privacy/
│   ├── sanitizer.py
│   ├── identity_filter.py
│   ├── secret_detector.py
│   ├── pii_detector.py
│   └── policy_engine.py
│
├── context/
│   ├── context_builder.py
│   ├── metric_selector.py
│   └── aggregator.py
│
└── providers/
    ├── local.py
    ├── cloud.py
    └── base.py
```

---

# 45. Policy Engine

The policy engine determines whether data can enter an AI request.

Conceptual rule:

```text
IF data.classification == SECRET
    → BLOCK

IF data.classification == PERSONAL
    → BLOCK_FOR_CLOUD

IF data.type == RAW_PROVIDER_EVENT
    → BLOCK_FOR_CLOUD

IF data.type == DEVELOPER_IDENTITY
    → BLOCK_FOR_CLOUD

IF data.classification == AI_SAFE
    → ALLOW
```

Default behavior:

```text
UNKNOWN → BLOCK
```

---

# 46. AI Data Contract

Every AI request should have an explicit data contract.

Example:

```json
{
  "scope": "PROJECT",
  "period": {
    "from": "2026-08-01",
    "to": "2026-08-20"
  },
  "metrics": {
    "engineering_health": 82,
    "deployment_frequency": 8.2,
    "change_failure_rate": 0.06
  },
  "trends": [
    "deployment_frequency_declining",
    "review_cycle_time_increasing"
  ]
}
```

No identity or secret fields are included.

---

# 47. Data Boundary Testing

The implementation must test the boundary explicitly.

## Test 1 — Developer Identity

Input:

```json
{
  "developer_name": "Test Developer"
}
```

Expected:

```text
BLOCKED
```

---

## Test 2 — API Key

Input:

```json
{
  "api_key": "secret-value"
}
```

Expected:

```text
BLOCKED
```

---

## Test 3 — Raw Provider Payload

Input:

```json
{
  "payload": {
    "full_provider_event": "..."
  }
}
```

Expected:

```text
BLOCKED
```

---

## Test 4 — Aggregated Metric

Input:

```json
{
  "deployment_frequency": 8.2
}
```

Expected:

```text
ALLOWED
```

subject to policy and context.

---

# 48. Privacy Acceptance Tests

The following must pass:

```text
- [ ] Developer names never reach cloud AI.
- [ ] Developer emails never reach cloud AI.
- [ ] Developer IDs never reach cloud AI.
- [ ] Provider access tokens never reach AI.
- [ ] API keys never reach AI.
- [ ] Raw provider payloads never reach cloud AI.
- [ ] Individual productivity scores do not exist.
- [ ] Unknown sensitive fields are blocked.
- [ ] Prompt injection from provider text is handled safely.
- [ ] AI requests use only approved context.
- [ ] AI failures do not break analytics.
- [ ] Offline core analytics continue.
```

---

# 49. Monitoring the AI Boundary

The system should monitor:

```text
AI requests
Blocked requests
Privacy violations
Secret detection events
Sanitization events
AI provider failures
AI response validation failures
AI latency
AI usage
```

Security events should be auditable.

---

# 50. Security Incident Flow

If prohibited data is detected:

```text
Sensitive Data Detected
        ↓
Block Request
        ↓
Do NOT send to AI
        ↓
Log Security Event
        ↓
Alert / Review if required
        ↓
Continue Application
```

The blocked data should not itself be copied into an external logging system.

---

# 51. Data Boundary Definition of Done

The AI Data Boundary is considered implemented when:

- [ ] AI Gateway exists.
- [ ] Context Builder exists.
- [ ] Privacy Filter exists.
- [ ] Identity filtering exists.
- [ ] Secret detection exists.
- [ ] Raw payload blocking exists.
- [ ] AI-safe data allowlist exists.
- [ ] Unknown data fails closed.
- [ ] Cloud AI cannot receive developer identity.
- [ ] Cloud AI cannot receive credentials.
- [ ] Cloud AI cannot receive secrets.
- [ ] Cloud AI cannot receive raw provider payloads.
- [ ] Individual productivity scores do not exist.
- [ ] Provider text is treated as untrusted input.
- [ ] Prompt injection protections exist.
- [ ] AI responses are validated.
- [ ] AI requests are auditable.
- [ ] Access control is enforced.
- [ ] Offline behavior works.
- [ ] AI failure does not break analytics.
- [ ] Privacy tests pass.

---

# 52. Locked AI Data Boundary Rules

These rules are **non-negotiable**:

```text
1. Developer identity must NEVER be sent to a cloud LLM.

2. Raw provider events must NEVER be sent directly
   to a cloud LLM.

3. Provider credentials must NEVER be sent to AI.

4. API keys and secrets must NEVER be sent to AI.

5. Individual productivity scores must NEVER be
   calculated, stored, exposed, or sent to AI.

6. AI requests must pass through the CodeSense
   AI Gateway.

7. AI requests must use approved/sanitized context.

8. Unknown data must be treated as unsafe.

9. Provider-generated text is untrusted input.

10. Cloud AI must never be a dependency for
    core CodeSense analytics.

11. Offline CodeSense must continue operating
    without cloud AI.

12. AI-generated information is an interpretation,
    not the source of truth.

13. Verified CodeSense analytics always take
    precedence over AI-generated claims.

14. AI boundary violations must fail closed.

15. Changes to these rules require explicit
    architectural review.
```

---

# 53. Relationship With Other CodeSense Documents

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

`AI_DATA_BOUNDARY.md` is the **security and privacy contract for all AI functionality** in CodeSense.

Any implementation that introduces a new AI provider, new AI feature, new data source, or new AI context field must be reviewed against this document before being implemented.