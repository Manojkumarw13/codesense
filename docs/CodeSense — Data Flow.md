# CodeSense — Data Flow

**Document Status:** Draft / Editable  
**Version:** 1.0  
**Project:** CodeSense  
**Purpose:** Define how engineering data moves through CodeSense from external providers to analytics, Engineering Health, dashboards, and AI insights.

---

# 1. Data Flow Overview

The primary CodeSense data pipeline is:

```text
External Engineering Platforms
            ↓
     Provider Adapters
            ↓
       Data Ingestion
            ↓
      Event Validation
            ↓
     Raw Event Storage
            ↓
   Canonical Transformation
            ↓
    Canonical Data Layer
            ↓
      Analytics Engine
            ↓
 Engineering Health Engine
            ↓
      ┌─────┴─────┐
      ↓           ↓
  Dashboard    AI Gateway
                  ↓
            Privacy Filter
                  ↓
              LLM
                  ↓
            AI Insights
```

The most important architectural rule is:

```text
Raw Data
   ↓
Canonical Data
   ↓
Analytics
   ↓
Engineering Health
   ↓
AI Insights
```

AI must not become the source of truth for engineering analytics.

---

# 2. Data Flow Principles

CodeSense follows these principles:

1. Raw provider events are preserved.
2. Raw data is never replaced by canonical data.
3. Canonical data provides a provider-independent analytical layer.
4. Analytics operate primarily on canonical data.
5. Engineering Health is calculated from approved engineering metrics.
6. Individual productivity scores are not calculated.
7. Developer identity must never be sent to cloud AI.
8. AI is optional for core functionality.
9. Core analytics work offline.
10. Provider integrations are isolated through adapters.
11. Processing must be idempotent.
12. Failed processing must be retryable.
13. Data lineage should remain traceable.

---

# 3. Complete End-to-End Flow

```text
┌───────────────────────────────┐
│ External Engineering Systems  │
│                               │
│ GitHub                        │
│ GitLab                        │
│ Jira                          │
│ CI/CD                         │
│ Other Providers               │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│ Provider Adapter Layer        │
│                               │
│ Authentication               │
│ API Client                   │
│ Webhook Handler              │
│ Provider Mapping              │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│ Event Ingestion               │
│                               │
│ Receive                       │
│ Validate                      │
│ Deduplicate                   │
│ Timestamp                     │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│ Raw Event Store               │
│                               │
│ Original Provider Payload     │
│ Provider Event ID             │
│ Event Type                    │
│ Received Time                 │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│ Processing Pipeline           │
│                               │
│ Classification                │
│ Validation                    │
│ Transformation               │
│ Normalization                 │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│ Canonical Data Layer          │
│                               │
│ Commit                        │
│ Pull Request                  │
│ Review                        │
│ Issue                         │
│ Deployment                    │
│ Build                         │
│ Incident                      │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│ Analytics Engine              │
│                               │
│ Aggregation                   │
│ Metrics                       │
│ Trends                        │
│ Anomaly Detection             │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│ Engineering Health Engine     │
│                               │
│ Delivery                      │
│ Quality                       │
│ Reliability                   │
│ Flow                          │
│ Other approved signals        │
└───────────────┬───────────────┘
                │
          ┌─────┴─────┐
          ▼           ▼
┌────────────────┐  ┌────────────────────┐
│ CodeSense UI   │  │ AI Gateway         │
│                │  │                    │
│ Dashboard      │  │ Privacy Filter     │
│ Analytics      │  │ Sanitization       │
│ Trends         │  │ Context Builder    │
│ Health         │  └─────────┬──────────┘
└────────────────┘            │
                              ▼
                    ┌────────────────────┐
                    │ Local / Cloud LLM  │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │ AI Insight         │
                    │ Validation         │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │ CodeSense UI       │
                    └────────────────────┘
```

---

# 4. Data Sources

CodeSense can receive engineering data from multiple external systems.

Examples:

```text
Source Control
├── GitHub
└── GitLab

Project Management
├── Jira
└── Other issue trackers

CI/CD
├── Build systems
├── Deployment systems
└── Pipeline platforms

Future Sources
├── Incident management
├── Code quality tools
└── Observability platforms
```

Each source must have a dedicated adapter.

---

# 5. Provider Adapter Flow

Each provider follows:

```text
Provider
   ↓
Provider Adapter
   ↓
Provider Authentication
   ↓
Fetch API Data / Receive Webhook
   ↓
Provider Event
   ↓
CodeSense Ingestion
```

The provider adapter is responsible for provider-specific behavior.

It should handle:

- Authentication
- API communication
- Webhook verification
- Provider event formats
- Provider-specific pagination
- Provider-specific retry behavior
- Provider-specific event mapping

It should not contain CodeSense analytics logic.

---

# 6. Webhook Data Flow

When a provider sends a webhook:

```text
External Provider
       ↓
Webhook Endpoint
       ↓
Signature Verification
       ↓
Connection Identification
       ↓
Event Validation
       ↓
Duplicate Detection
       ↓
Raw Event Storage
       ↓
Queue / Background Worker
       ↓
Canonical Transformation
```

The webhook endpoint should return quickly.

Heavy processing must happen asynchronously.

---

# 7. API Polling Flow

Some providers may require scheduled polling.

```text
Scheduler
    ↓
Provider Connection
    ↓
Provider API
    ↓
Fetch New Events
    ↓
Deduplicate
    ↓
Raw Event Store
    ↓
Processing Queue
```

Polling must track synchronization state.

Example:

```text
last_sync_at
cursor
page_token
provider_checkpoint
```

---

# 8. Raw Event Flow

Every incoming provider event first enters the raw layer.

```text
Provider Event
      ↓
Validation
      ↓
Raw Provider Event
      ↓
PostgreSQL
```

The raw event contains:

```text
provider_connection_id
provider_event_id
event_type
received_at
payload
payload_hash
source_url
processing_status
```

The original payload must remain unchanged.

---

# 9. Raw Event Immutability

The raw event flow is:

```text
Incoming Event
      ↓
INSERT
      ↓
Raw Event
      ↓
Immutable Payload
```

Only processing metadata may change.

Allowed:

```text
processing_status
processed_at
```

Not allowed:

```text
payload modification
provider_event_id modification
original event type modification
original timestamp modification
```

---

# 10. Event Deduplication

CodeSense must prevent duplicate processing.

Deduplication key:

```text
provider_connection_id
        +
provider_event_id
```

Flow:

```text
Incoming Event
      ↓
Check Event ID
      ↓
Already Exists?
   ┌──┴──┐
  YES    NO
   │      │
   ▼      ▼
Ignore   Store
```

This ensures repeated webhooks do not generate duplicate analytics.

---

# 11. Event Processing Flow

After raw storage:

```text
Raw Event
    ↓
Processing Worker
    ↓
Event Classification
    ↓
Schema Validation
    ↓
Provider Mapping
    ↓
Canonical Transformation
    ↓
Canonical Event
```

Failures should not destroy the raw event.

---

# 12. Failed Event Flow

```text
Raw Event
    ↓
Processing
    ↓
Failure
    ↓
Retry
    ↓
Processing
```

If repeated retries fail:

```text
Retry Limit
     ↓
Failed Job
     ↓
Error Logging
     ↓
Manual / Automated Recovery
```

The original raw event remains available for reprocessing.

---

# 13. Canonical Transformation

The canonical layer converts different provider formats into a common model.

Example:

```text
GitHub Pull Request
        │
GitLab Merge Request
        │
        ▼
Canonical Pull Request Event
```

Another example:

```text
GitHub Commit
GitLab Commit
       ↓
Canonical Commit Event
```

---

# 14. Canonical Event Structure

A canonical event should conceptually contain:

```text
id
raw_event_id
organization_id
team_id
project_id
repository_id
event_type
occurred_at
actor_ref
entity_type
entity_id
metadata
created_at
```

The canonical model must not depend on a single provider.

---

# 15. Data Lineage

Every canonical event should be traceable back to its raw source.

```text
Canonical Event
      ↓
raw_event_id
      ↓
Raw Provider Event
      ↓
Provider Connection
      ↓
External Provider
```

This enables:

- Debugging
- Auditing
- Reprocessing
- Data validation
- Historical analysis

---

# 16. Example Pull Request Flow

```text
Developer creates Pull Request
             ↓
GitHub
             ↓
GitHub Webhook
             ↓
CodeSense Webhook API
             ↓
Raw Event Store
             ↓
Processing Worker
             ↓
Canonical Pull Request Event
             ↓
Analytics Engine
             ↓
Review Cycle Metrics
             ↓
Engineering Health
             ↓
Dashboard
```

---

# 17. Example Deployment Flow

```text
Deployment Pipeline
       ↓
Deployment Event
       ↓
Provider Adapter
       ↓
Raw Event
       ↓
Canonical Deployment Event
       ↓
Analytics
       ↓
Deployment Frequency
       ↓
Change Performance
       ↓
Engineering Health
```

---

# 18. Analytics Data Flow

Analytics should operate primarily on canonical data.

```text
Canonical Events
       ↓
Metric Calculation
       ↓
Metric Values
       ↓
Aggregation
       ↓
Analytics Snapshot
       ↓
Trend Detection
       ↓
Dashboard
```

Analytics should not repeatedly parse raw provider payloads when an appropriate canonical representation exists.

---

# 19. Metric Calculation

Conceptually:

```text
Canonical Events
       ↓
Filter by period
       ↓
Filter by project/team
       ↓
Group events
       ↓
Calculate metric
       ↓
Store metric value
```

Example:

```text
Deployment Events
       ↓
Count successful deployments
       ↓
Deployment Frequency
```

---

# 20. Engineering Health Flow

```text
Approved Engineering Metrics
           ↓
Metric Normalization
           ↓
Component Scores
           ↓
Weighted / Defined Calculation
           ↓
Engineering Health Score
           ↓
Historical Storage
           ↓
Dashboard
```

Possible components:

```text
Delivery
Quality
Reliability
Flow
Code Review
Deployment
```

The exact scoring formula must be defined separately in the Engineering Health specification.

---

# 21. Individual Productivity Restriction

The data flow must never become:

```text
Developer
   ↓
Activity Count
   ↓
Productivity Score
```

This flow is prohibited.

Instead:

```text
Engineering Events
      ↓
Aggregated Operational Metrics
      ↓
Team / Project Engineering Health
```

Individual operational metrics may exist when necessary, but they must not be transformed into individual productivity scores.

---

# 22. Dashboard Data Flow

The dashboard does not directly query raw provider systems.

```text
External Providers
       ↓
CodeSense Processing
       ↓
Canonical Data
       ↓
Analytics
       ↓
Cached / Stored Results
       ↓
API
       ↓
Dashboard
```

The frontend receives structured API responses.

---

# 23. Dashboard Request Flow

Example:

```text
User opens Dashboard
        ↓
GET /api/v1/analytics/dashboard
        ↓
Authentication
        ↓
Authorization
        ↓
Query Analytics
        ↓
Return Metrics
        ↓
Render Dashboard
```

---

# 24. AI Data Flow

AI is a downstream consumer of approved analytical information.

```text
Analytics
    ↓
Insight Preparation
    ↓
Privacy Sanitization
    ↓
AI Context
    ↓
AI Gateway
    ↓
Local / Cloud LLM
    ↓
Response Validation
    ↓
AI Insight
    ↓
Database
    ↓
Dashboard
```

The AI layer must never bypass the analytics and privacy layers.

---

# 25. AI Privacy Boundary

The following flow is mandatory:

```text
CodeSense Analytics
        ↓
Sanitization
        ↓
Remove Developer Identity
        ↓
Remove Secrets
        ↓
Remove Credentials
        ↓
Remove Sensitive Raw Data
        ↓
Approved Analytical Context
        ↓
Cloud LLM
```

---

# 26. Prohibited AI Flow

The following is strictly prohibited:

```text
Raw Provider Event
       ↓
Cloud LLM
```

Also prohibited:

```text
Developer Database Record
       ↓
Cloud LLM
```

And:

```text
Developer Identity
       ↓
Cloud LLM
```

---

# 27. AI Insight Example

Correct flow:

```text
Analytics:

Review cycle time
Deployment frequency
Change failure rate
Engineering Health trend

        ↓

Privacy Sanitization

        ↓

AI Context:

"Review cycle time increased by 18%
during the selected period."

        ↓

LLM

        ↓

Insight:

"Review cycle time increased during
the selected period, suggesting a
potential review bottleneck."

        ↓

Dashboard
```

No developer identity is required.

---

# 28. AI Failure Flow

If the AI provider fails:

```text
AI Request
     ↓
AI Gateway
     ↓
Provider Failure
     ↓
Fallback / Error
     ↓
AI Insight Unavailable
```

Meanwhile:

```text
Analytics
    ↓
Engineering Health
    ↓
Dashboard
```

continues operating.

AI failure must not stop core CodeSense analytics.

---

# 29. Offline Data Flow

Offline operation is a core architectural requirement.

```text
                OFFLINE MODE

Local Engineering Data
          ↓
Local Provider Adapter
          ↓
Raw Event Store
          ↓
Canonical Processing
          ↓
Analytics
          ↓
Engineering Health
          ↓
Dashboard
```

No cloud dependency should exist in this path.

---

# 30. Offline AI Flow

When cloud AI is unavailable:

```text
Analytics
     ↓
AI Gateway
     ↓
Cloud unavailable
     ↓
AI unavailable
```

But:

```text
Analytics
     ↓
Engineering Health
     ↓
Dashboard
```

must continue.

If a local LLM is configured, the AI Gateway may route to it according to deployment configuration.

---

# 31. Synchronization After Offline Mode

When connectivity returns:

```text
Internet Restored
       ↓
Provider Connection
       ↓
Determine Last Checkpoint
       ↓
Fetch Missing Events
       ↓
Deduplicate
       ↓
Raw Event Store
       ↓
Canonical Processing
       ↓
Analytics Recalculation
```

Previously stored local events must not be duplicated.

---

# 32. Data Flow Between Services

```text
Frontend
   ↓
API
   ↓
Application Services
   ↓
Processing Services
   ↓
PostgreSQL
```

For asynchronous work:

```text
API
 ↓
Job Queue
 ↓
Worker
 ↓
Processing
 ↓
PostgreSQL
```

---

# 33. Event Queue Flow

For high-volume processing:

```text
Provider Event
      ↓
Raw Event Store
      ↓
Job Queue
      ↓
Worker
      ↓
Canonical Transformation
      ↓
Analytics
```

The queue should provide:

- Retry
- Failure handling
- Job status
- Concurrency control
- Back-pressure handling

---

# 34. Data Flow for Multiple Providers

```text
               ┌── GitHub ────────┐
               │                  │
               ├── GitLab ────────┤
               │                  │
               └── Jira ──────────┘
                        │
                        ▼
                Provider Adapters
                        │
                        ▼
                 Raw Event Store
                        │
                        ▼
               Canonical Data Layer
                        │
                        ▼
                 Analytics Engine
                        │
                        ▼
             Provider-Independent Data
```

The analytics layer should not need separate implementations for every provider.

---

# 35. Cross-Provider Analytics

Example:

```text
GitHub PRs
GitLab MRs
       ↓
Canonical Pull Requests
       ↓
Review Metrics
       ↓
Unified Analytics
```

This is one of the primary reasons for the canonical data layer.

---

# 36. Data Ownership

| Data | Source of Truth |
|---|---|
| Provider event | Raw Event Store |
| Canonical event | Canonical Data Layer |
| Metric | Analytics Database |
| Engineering Health | Health Score Table |
| AI insight | AI Insights Table |
| User identity | Identity Database |
| Configuration | Configuration Database |
| Audit event | Audit Log |

---

# 37. Data Processing States

Raw events may follow:

```text
RECEIVED
   ↓
VALIDATED
   ↓
QUEUED
   ↓
PROCESSING
   ↓
PROCESSED
```

Failure path:

```text
PROCESSING
    ↓
FAILED
    ↓
RETRYING
    ↓
PROCESSING
```

Final failure:

```text
FAILED
    ↓
DEAD_LETTER / MANUAL_REVIEW
```

The exact implementation can use a queue-specific terminology.

---

# 38. Data Quality Checks

Before canonical transformation:

```text
Event Received
     ↓
Schema Validation
     ↓
Provider Validation
     ↓
Required Fields Check
     ↓
Duplicate Check
     ↓
Timestamp Validation
     ↓
Canonical Transformation
```

Invalid events must not silently enter the analytical layer.

---

# 39. Data Quality Failure

```text
Invalid Event
      ↓
Raw Event Preserved
      ↓
Processing Failure
      ↓
Error Recorded
      ↓
Retry / Manual Review
```

The raw payload remains available.

---

# 40. Security Data Flow

Every user request follows:

```text
User
 ↓
Authentication
 ↓
Token Validation
 ↓
Organization Validation
 ↓
Role Validation
 ↓
Resource Authorization
 ↓
Service
 ↓
Database
```

Unauthorized data must never reach the client.

---

# 41. Audit Data Flow

Important actions follow:

```text
User Action
     ↓
API
     ↓
Authorization
     ↓
Business Operation
     ↓
Audit Event
     ↓
Audit Log
```

Examples:

```text
Provider connected
Project created
Role changed
Configuration changed
AI insight generated
Sensitive data accessed
```

---

# 42. Data Export Flow

If CodeSense supports exports:

```text
User
 ↓
Export Request
 ↓
Authorization
 ↓
Analytics Query
 ↓
Data Filtering
 ↓
Export Generation
 ↓
Audit Log
 ↓
Download
```

Exports must respect the user's access permissions.

---

# 43. Data Deletion Flow

Deletion must be handled carefully because raw events may be required for auditability.

Conceptual flow:

```text
Deletion Request
       ↓
Validate Policy
       ↓
Check Dependencies
       ↓
Apply Retention Rules
       ↓
Delete / Anonymize
       ↓
Audit Action
```

Deletion behavior must comply with the final data-retention and privacy policy.

---

# 44. Data Retention Flow

Different data classes may have different retention policies.

```text
Raw Events
     ↓
Retention Policy
     ↓
Archive / Delete

Canonical Events
     ↓
Retention Policy
     ↓
Archive / Delete

Analytics
     ↓
Long-Term Retention

Audit Logs
     ↓
Policy-Based Retention

AI Insights
     ↓
Policy-Based Retention
```

Retention periods should be configurable where appropriate.

---

# 45. Data Recovery Flow

If canonical processing fails:

```text
Canonical Data Missing
        ↓
Find Raw Event
        ↓
Reprocess
        ↓
Canonical Transformation
        ↓
Analytics Recalculation
```

This is why raw events must be preserved.

---

# 46. Reprocessing Flow

```text
Raw Event
    ↓
Replay Request
    ↓
Validation
    ↓
Canonical Transformation
    ↓
Canonical Event
    ↓
Analytics Recalculation
```

Reprocessing must be idempotent.

---

# 47. Data Flow Monitoring

The system should monitor:

```text
Events received
Events processed
Events failed
Events retried
Processing latency
Queue depth
Provider sync status
Analytics processing time
AI request status
```

Example:

```text
Provider
   ↓
1000 events
   ↓
995 processed
   ↓
3 retrying
   ↓
2 failed
```

---

# 48. End-to-End Example

A complete example:

```text
1. Developer creates Pull Request
             ↓
2. GitHub sends webhook
             ↓
3. CodeSense validates webhook
             ↓
4. Raw event is stored
             ↓
5. Job is queued
             ↓
6. Worker processes event
             ↓
7. Canonical PR event created
             ↓
8. Review metrics updated
             ↓
9. Engineering Health recalculated
             ↓
10. Dashboard displays updated metrics
             ↓
11. User requests AI explanation
             ↓
12. Analytics context prepared
             ↓
13. Developer identity removed
             ↓
14. Sanitized context sent to AI Gateway
             ↓
15. LLM generates explanation
             ↓
16. Response validated
             ↓
17. Insight stored
             ↓
18. Dashboard displays insight
```

---

# 49. Complete Architecture Data Flow

```text
                         EXTERNAL WORLD
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
     GitHub                 GitLab              CI/CD/Jira
        │                     │                     │
        └──────────────┬──────┴──────┬──────────────┘
                       ▼             ▼
                Provider Adapters
                       │
                       ▼
                 Data Ingestion
                       │
                       ▼
               Validation / Dedup
                       │
                       ▼
                RAW EVENT STORE
                       │
                       ▼
                Processing Queue
                       │
                       ▼
             Canonical Transformation
                       │
                       ▼
             CANONICAL DATA LAYER
                       │
             ┌─────────┼─────────┐
             │         │         │
             ▼         ▼         ▼
          Metrics   Trends   Aggregations
             │         │         │
             └─────────┼─────────┘
                       ▼
             ENGINEERING HEALTH
                       │
             ┌─────────┴──────────┐
             │                    │
             ▼                    ▼
        CodeSense UI          AI Gateway
                                  │
                           Privacy Filter
                                  │
                         ┌────────┴────────┐
                         ▼                 ▼
                     Local LLM         Cloud LLM
                         │                 │
                         └────────┬────────┘
                                  ▼
                            AI Validation
                                  │
                                  ▼
                              AI Insights
                                  │
                                  ▼
                            CodeSense UI
```

---

# 50. Locked Data Flow Constraints

The following are non-negotiable:

```text
1. Every provider event must first be preserved
   as raw data.

2. Raw provider payloads must remain untouched.

3. Raw events must remain available for reprocessing.

4. Cross-provider analytics must use the canonical
   analytical layer.

5. Provider-specific logic must remain in provider adapters.

6. Individual productivity scores must never be calculated.

7. Individual operational metrics must remain
   privacy/access controlled.

8. Developer identity must never be sent to a
   cloud LLM.

9. Raw provider payloads must never be sent directly
   to a cloud LLM.

10. Secrets and credentials must never be sent
    to a cloud LLM.

11. AI must operate behind the AI Gateway.

12. AI must not be required for core analytics.

13. Core analytics must continue in offline mode.

14. Provider events must be processed idempotently.

15. Failed processing must not destroy raw events.

16. Canonical events must maintain lineage to raw events.

17. All important data access must respect
    organization and role permissions.
```

---

# 51. Definition of Done

The CodeSense data-flow implementation is complete when:

- [ ] Provider adapters are implemented.
- [ ] Webhook ingestion works.
- [ ] Polling/synchronization works where required.
- [ ] Raw events are preserved.
- [ ] Event deduplication works.
- [ ] Background processing works.
- [ ] Failed events can be retried.
- [ ] Canonical events are generated.
- [ ] Canonical events maintain raw-event lineage.
- [ ] Analytics operate on canonical data.
- [ ] Engineering Health is calculated.
- [ ] Individual productivity scoring does not exist.
- [ ] Dashboard receives analytical data through the API.
- [ ] AI requests pass through the privacy boundary.
- [ ] Developer identity is removed before cloud AI.
- [ ] Raw provider payloads never reach cloud AI.
- [ ] AI failures do not break analytics.
- [ ] Offline analytics work.
- [ ] Synchronization resumes correctly after reconnect.
- [ ] Data quality failures are traceable.
- [ ] Reprocessing works.
- [ ] Audit logging works.
- [ ] End-to-end tests pass.

---

# 52. Relationship With Other Documents

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

`DATA_FLOW.md` defines the **movement and transformation of information** throughout CodeSense.

It must remain synchronized with:

- `DATABASE_SCHEMA.md`
- `API_SPECIFICATION.md`
- `SYSTEM_ARCHITECTURE.md`
- `AI_DATA_BOUNDARY.md`
- `ACCEPTANCE_TESTS.md`

Any change to the data pipeline should be reflected in this document.