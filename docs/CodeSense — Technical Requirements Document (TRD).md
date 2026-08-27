# CodeSense — Technical Requirements Document (TRD)

**Version:** 1.0  
**Date:** August 18, 2026  
**Project:** Mini Project-I  
**System:** CodeSense Engineering Analytics Platform  
**Document Type:** Technical Requirements Document

---

# 1. Purpose

This Technical Requirements Document defines the technical architecture, system requirements, data model, APIs, processing pipeline, privacy controls, infrastructure, security requirements, and implementation constraints for **CodeSense**.

CodeSense is a **provider-agnostic, privacy-preserving engineering analytics platform** that transforms engineering activity from multiple development tools into a canonical analytical model and generates team-level engineering insights.

The technical design must preserve the following locked project principles:

1. Raw provider events remain untouched.
2. A canonical analytical layer is created for cross-provider analytics.
3. Individual productivity scores are completely excluded.
4. Developer identity must never be sent to cloud LLM providers.
5. Core analytics must continue operating without Internet connectivity.
6. Cloud-AI functionality is optional.
7. Engineering Health Score is team-level and explainable.
8. The real-time simulator is a data-generation component, not the CodeSense product itself.
9. Provider-specific integrations must be modular.
10. Analytics must measure engineering-system health rather than individual developer performance.

---

# 2. Technical Objectives

The system shall:

- Ingest engineering events from multiple providers.
- Accept simulated real-time events.
- Preserve raw events immutably.
- Normalize provider events into canonical events.
- Store canonical entities and relationships.
- Calculate engineering metrics.
- Calculate an explainable Engineering Health Score.
- Detect engineering bottlenecks.
- Detect statistical/behavioral anomalies.
- Generate historical trends.
- Provide dashboards through APIs.
- Support optional AI-powered explanations.
- Prevent developer identity from reaching cloud AI services.
- Operate core analytics without Internet access.
- Support future provider integrations without rewriting the analytics engine.

---

# 3. System Architecture

## 3.1 Logical Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                    External Data Sources                     │
│                                                              │
│      GitHub │ GitLab │ Jira │ CI/CD │ Deployments            │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                     Connector Layer                          │
│                                                              │
│ Provider Adapters → Event Extraction → Validation            │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                    Ingestion Service                         │
│                                                              │
│ REST API │ Webhook Receiver │ Batch Import │ Simulator       │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                     Raw Event Store                          │
│                                                              │
│ Immutable Provider Events                                    │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                 Normalization / Mapping Layer                │
│                                                              │
│ Provider Event → Canonical Event                             │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                  Canonical Data Layer                        │
│                                                              │
│ Teams │ Repositories │ Work Items │ Changes │ Reviews        │
│ Builds │ Deployments │ Incidents │ Engineering Events       │
└─────────────────────────────┬────────────────────────────────┘
                              │
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
       ┌─────────────┐ ┌─────────────┐ ┌──────────────┐ ┌──────────────┐
       │ Metric      │ │ Health Score│ │ Trend /      │ │ ML Engine    │
       │ Engine      │ │ Engine      │ │ Anomaly      │ │ & Prediction │
       └──────┬──────┘ └──────┬──────┘ └──────┬───────┘ └──────┬───────┘
              └───────────────┼────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                     Fusion Layer                             │
│ Rules + Stats + ML (Evidence & Confidence)                   │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                    Insight Layer                             │
│                                                              │
│ Bottlenecks │ Anomalies │ Risk Predictions │ Recommendations │
└─────────────────────────────┬────────────────────────────────┘
                              │
                  ┌───────────┴────────────┐
                  ▼                        ▼
          ┌──────────────┐         ┌──────────────┐
          │ Dashboard /  │         │ Optional     │
          │ REST API     │         │ AI Layer     │
          └──────────────┘         └──────────────┘
```

---

# 4. Architectural Principles

## TR-001 — Modular Architecture

Each major subsystem shall have a clear responsibility and interface.

Required modules:

```text
connectors/
ingestion/
raw_storage/
normalization/
canonical/
metrics/
health_score/
anomaly_detection/
ml/
insights/
privacy/
ai/
api/
simulator/
```

---

## TR-002 — Provider Independence

The metric engine shall never directly depend on GitHub, GitLab, Jira, or another provider's proprietary event schema.

The dependency chain shall be:

```text
Provider
   ↓
Connector
   ↓
Provider Event
   ↓
Canonical Event
   ↓
Analytics
```

Not:

```text
GitHub API
   ↓
Metric Engine
```

---

## TR-003 — Layer Separation

Raw data, normalized data, analytical data, and presentation data must remain logically separated.

```text
Raw
 ↓
Canonical
 ↓
Analytical
 ↓
Aggregated
 ↓
Presentation
```

---

# 5. Technology Requirements

## 5.1 Recommended Backend

**Python + FastAPI**

Reasons:

- Strong data-processing ecosystem
- Good REST API support
- Pydantic validation
- Async capabilities
- Easy integration with ML/AI libraries (`scikit-learn`, `xgboost`, `prophet`)
- Suitable for the simulator
- Suitable for academic prototype development

---

## 5.2 Database

**PostgreSQL**

Primary responsibilities:

- Canonical entities
- Engineering events
- Metrics
- Aggregations
- Teams
- Repositories
- Configuration
- Health scores
- Anomaly records

---

## 5.3 Cache / Message Infrastructure

**Redis** may be used for:

- Short-lived caching
- Event queues
- Background processing
- Rate limiting
- Temporary state

Redis is optional for the first MVP if PostgreSQL-backed processing is sufficient.

---

## 5.4 Data Processing

Required:

- Python
- Pandas
- NumPy

Optional:

- Polars for higher-volume analytical processing

---

## 5.5 Frontend

Strict Standard:

- React
- TypeScript
- Recharts/Plotly or equivalent

---

## 5.6 Containerization

The system should be containerized using:

- Docker
- Docker Compose

## 5.7 Infrastructure & Observability

Refer to `INFRASTRUCTURE.md` for complete requirements. Core elements include:
- Redis (caching, queues)
- Prometheus & Grafana (metrics)
- OpenTelemetry (distributed tracing)

---

# 6. Component Requirements

# 6.1 Connector Layer

The connector layer is responsible for communicating with external engineering systems.

### Requirements

Each connector shall implement a common interface.

Example conceptual interface:

```python
class ProviderConnector:
    def authenticate(self):
        ...

    def fetch_events(self, start_time, end_time):
        ...

    def normalize_event(self, event):
        ...
```

Provider-specific implementation should remain isolated.

---

## 6.1.1 Connector Responsibilities

Connectors shall:

1. Authenticate with provider.
2. Retrieve provider events.
3. Handle pagination.
4. Handle API rate limits.
5. Handle provider errors.
6. Track synchronization state.
7. Preserve original event payload.
8. Pass events to ingestion.

---

# 6.2 Ingestion Service

The ingestion service shall provide multiple ingestion mechanisms.

### Supported mechanisms

```text
REST API
Webhook
Batch Import
Simulator
```

### Example endpoints

```text
POST /api/v1/events
POST /api/v1/events/batch
POST /api/v1/webhooks/{provider}
```

---

## 6.2.1 Event Validation

Every event shall be validated for:

- Provider
- Event type
- Event ID
- Timestamp
- Payload structure
- Required metadata

Invalid events shall be rejected or quarantined rather than silently processed.

---

# 6.3 Raw Event Storage

The raw layer is an immutable record of what the provider sent.

Example:

```json
{
  "event_id": "provider-event-123",
  "provider": "github",
  "event_type": "pull_request",
  "received_at": "2026-08-18T15:30:00Z",
  "payload": {
    "...": "original provider payload"
  }
}
```

### Requirements

- Original payload must not be modified.
- Provider metadata must be preserved.
- Ingestion timestamp must be stored.
- Source/provider must be recorded.
- Duplicate detection must be supported.
- Raw events must be retrievable by authorized users/services.

---

# 6.8 ML Engine

The ML Engine manages model training and inference.
1. **Feature Pipeline**: Transforms canonical data into ML features.
2. **Model Registry**: Tracks global models (adapted to orgs/teams). No individual modeling.
3. **Inference API**: Serves predictions (risk, anomalies) internally to the FusionEngine.

---

# 6.4 Canonicalization Layer

The canonicalization layer converts provider-specific events into CodeSense events.

Example:

```text
GitHub:
pull_request.opened

GitLab:
merge_request.created

        ↓

CodeSense:
CHANGE_REVIEW_REQUESTED
```

---

## 6.4.1 Canonical Event Structure

Example:

```json
{
  "canonical_event_id": "evt_123",
  "source_event_id": "github_456",
  "provider": "github",
  "event_type": "CHANGE_REVIEW_REQUESTED",
  "occurred_at": "2026-08-18T15:30:00Z",
  "organization_id": "org_01",
  "team_id": "team_01",
  "project_id": "proj_01",
  "repository_id": "repo_01",
  "actor_ref": "internal_ref",
  "metadata": {}
}
```

`actor_ref` must not be included in cloud AI payloads.

---

# 7. Canonical Data Model

## 7.1 Organization

```text
organization
-------------
id
name
created_at
```

---

## 7.2 Team

```text
team
-------------
id
organization_id
name
created_at
```

---

## 7.3 Repository

```text
repository
-------------
id
team_id
provider
external_id
name
created_at
```

---

## 7.4 Work Item

```text
work_item
-------------
id
provider
external_id
team_id
repository_id
type
status
created_at
started_at
completed_at
```

---

## 7.5 Change

```text
change
-------------
id
provider
external_id
repository_id
team_id
created_at
merged_at
status
```

---

## 7.6 Review

```text
review
-------------
id
change_id
created_at
completed_at
status
```

Individual reviewer identity may be retained internally where necessary for event integrity and authorization but shall not be converted into a productivity score.

---

## 7.7 Build

```text
build
-------------
id
provider
external_id
repository_id
started_at
completed_at
status
duration
```

---

## 7.8 Deployment

```text
deployment
-------------
id
provider
external_id
repository_id
environment
started_at
completed_at
status
```

---

## 7.9 Incident

```text
incident
-------------
id
provider
external_id
team_id
severity
created_at
acknowledged_at
resolved_at
status
```

---

# 8. Engineering Event Model

Canonical event types should include at minimum:

```text
WORK_ITEM_CREATED
WORK_ITEM_STARTED
WORK_ITEM_COMPLETED

CHANGE_CREATED
CHANGE_UPDATED
CHANGE_MERGED
CHANGE_CLOSED

REVIEW_REQUESTED
REVIEW_STARTED
REVIEW_COMPLETED

BUILD_STARTED
BUILD_COMPLETED
BUILD_FAILED
BUILD_SUCCEEDED

DEPLOYMENT_STARTED
DEPLOYMENT_COMPLETED
DEPLOYMENT_FAILED
DEPLOYMENT_ROLLED_BACK

INCIDENT_CREATED
INCIDENT_ACKNOWLEDGED
INCIDENT_RESOLVED
```

Additional event types may be added without changing the core analytical architecture.

---

# 9. Event Processing Pipeline

The processing pipeline shall follow:

```text
Receive
   ↓
Validate
   ↓
Deduplicate
   ↓
Persist Raw Event
   ↓
Normalize
   ↓
Persist Canonical Event
   ↓
Update Analytical State
   ↓
Calculate Metrics
   ↓
Evaluate Health
   ↓
Detect Anomalies
   ↓
Generate Insights
```

Processing failures must not cause loss of the original raw event.

---

# 10. Idempotency

The ingestion pipeline must be idempotent.

A repeated provider event must not create duplicate analytical records.

Preferred uniqueness key:

```text
provider + external_event_id
```

Where provider event IDs are unavailable, a deterministic event fingerprint should be generated.

---

# 11. Metric Engine

The metric engine shall calculate metrics from canonical events rather than raw provider payloads.

## 11.1 Delivery Metrics

### Deployment Frequency

```text
deployment_frequency =
successful deployments / time period
```

### Lead Time for Changes

```text
lead_time =
deployment_time - change_start_time
```

### Cycle Time

```text
cycle_time =
completion_time - work_start_time
```

---

# 11.2 Review Metrics

### Review Turnaround

```text
review_turnaround =
review_completion_time - review_request_time
```

### Review Backlog

Number of changes awaiting review during a time interval.

### PR/MR Cycle Time

```text
merge_time - creation_time
```

---

# 11.3 CI/CD Metrics

### Build Success Rate

```text
successful_builds / total_builds
```

### Build Failure Rate

```text
failed_builds / total_builds
```

### Pipeline Duration

```text
completion_time - start_time
```

---

# 11.4 Reliability Metrics

### Change Failure Rate

```text
failed_changes / total_changes
```

### MTTR

```text
incident_resolution_time -
incident_start_time
```

### Deployment Failure Rate

```text
failed_deployments / total_deployments
```

---

# 12. Metric Calculation Requirements

Metrics shall support:

- Team aggregation
- Repository aggregation
- Daily aggregation
- Weekly aggregation
- Monthly aggregation
- Custom time ranges

Metric calculations must be deterministic given the same input data.

---

# 13. Engineering Health Score

The Health Score engine shall produce a team-level score.

Example conceptual weighting:

```text
Engineering Health Score
│
├── Delivery Flow       20%
├── Development Flow    20%
├── Review Flow         15%
├── CI/CD Reliability   15%
├── Deployment Health   15%
└── Operational Health  15%
```

The exact weights must remain configurable.

---

## 13.1 Score Requirements

The score shall:

- Be team-level.
- Be explainable.
- Use multiple metrics.
- Support configurable weights.
- Support historical comparison.
- Show contributing dimensions.
- Avoid individual developer scoring.
- Avoid treating the score as an absolute measure of engineering quality.

---

## 13.2 Score Output

Example:

```json
{
  "team_id": "team_01",
  "score": 78,
  "dimensions": {
    "delivery_flow": 82,
    "development_flow": 80,
    "review_flow": 71,
    "cicd_reliability": 85,
    "deployment_health": 76,
    "operational_health": 74
  }
}
```

---

# 14. Bottleneck Detection Engine

The bottleneck engine shall identify abnormal delays or accumulation in workflow stages.

## 14.1 Review Bottleneck

Trigger conditions may include:

```text
review_backlog ↑
AND
review_turnaround ↑
```

---

## 14.2 CI Bottleneck

Trigger conditions may include:

```text
pipeline_duration ↑
OR
build_queue ↑
OR
failure_rate ↑
```

---

## 14.3 Deployment Bottleneck

Trigger conditions may include:

```text
deployment_failure_rate ↑
OR
rollback_rate ↑
OR
deployment_duration ↑
```

---

# 15. ML-Powered Anomaly & Hybrid Detection

The detection system must use a hybrid approach (FusionEngine) merging:

### Statistical Rules
- Z-score `z = (x - μ) / σ`
- Rolling baseline (7-day / 30-day)
- Percentage change

### ML Methods
- Prophet (time-series forecasting)
- Isolation Forests (multivariate anomalies)

The detection system must record:

```text
anomaly_id
metric
team
detected_at
baseline
observed_value
severity
confidence
```

---

# 16. Risk Prediction

The platform shall predict engineering risks via ML (e.g., `xgboost`).
Examples include:
- Likelihood of a deployment failure.
- Likelihood of an incident spike.

Requirements for risk prediction:
- Outputs must include a probability/risk score.
- Must provide Evidence (contributing metrics/factors).
- Must provide a Confidence level.
- Must be calculated at the Team or Organization level (never Individual).

---

# 16.1 Insight Engine

The insight engine converts analytical results into structured insights.

Example:

```json
{
  "type": "BOTTLENECK",
  "category": "REVIEW_FLOW",
  "severity": "MEDIUM",
  "team_id": "team_01",
  "evidence": [
    {
      "metric": "review_turnaround",
      "change_percent": 28
    },
    {
      "metric": "review_backlog",
      "change_percent": 34
    }
  ]
}
```

Insights should always retain links to their supporting metrics.

---

# 17. AI Layer

The AI layer is optional.

It must sit above the analytics layer.

```text
Raw Data
   X
   │
   │ Never directly send raw data to cloud AI
   ▼
Canonical Analytics
   ↓
Team Aggregation
   ↓
Privacy Filter
   ↓
AI Request
```

---

# 18. AI Privacy Gateway

Before any cloud LLM request:

```text
Analytics Result
      ↓
PII Detection
      ↓
Identity Removal
      ↓
Payload Minimization
      ↓
Aggregation Verification
      ↓
Cloud LLM
```

The gateway must reject a request if prohibited identity information remains.

---

## 18.1 Prohibited Cloud AI Data

Cloud AI requests must not contain:

- Developer names
- Email addresses
- Personal usernames
- Developer IDs
- Personal access tokens
- Raw provider payloads containing identity
- Individual productivity measurements

---

## 18.2 Allowed AI Data

Example:

```json
{
  "team_metrics": {
    "lead_time_hours": 22.1,
    "review_turnaround_hours": 10.4,
    "deployment_frequency": 18,
    "change_failure_rate": 0.07
  },
  "period": "2026-W33"
}
```

---

# 19. Offline Architecture

Core CodeSense components shall not depend on a cloud LLM.

```text
                 OFFLINE
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
   Data Processing          Analytics
        │                       │
        └───────────┬───────────┘
                    ▼
              Dashboard
```

Cloud AI exists as an optional branch:

```text
Analytics
    │
    ▼
Privacy Gateway
    │
    ▼
Cloud LLM
```

If the cloud connection fails:

```text
AI unavailable
      ↓
Core analytics continues
```

---

# 20. Simulator Technical Requirements

The simulator shall generate events according to configurable scenarios.

## Required scenarios

```text
NORMAL
HIGH_LOAD
REVIEW_BOTTLENECK
CI_BOTTLENECK
DEPLOYMENT_FAILURE
INCIDENT_SPIKE
RECOVERY
```

---

## 20.1 Simulator Configuration

Example:

```yaml
scenario: review_bottleneck

teams: 3
repositories_per_team: 2
events_per_minute: 30

review_delay_multiplier: 2.5
deployment_failure_rate: 0.03
incident_rate: 0.01
```

---

## 20.2 Simulator Requirements

The simulator must:

- Generate deterministic events when seeded.
- Generate realistic timestamps.
- Generate relationships between entities.
- Generate correlated events.
- Support adjustable event rates.
- Support scenario switching.
- Support start/stop controls.
- Send events through the same ingestion interface used by real providers.

The simulator should **not bypass the ingestion pipeline**.

---

# 21. REST API

API prefix:

```text
/api/v1
```

---

## 21.1 Health

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

## 21.2 Events

```http
POST /api/v1/events
POST /api/v1/events/batch
GET /api/v1/events
```

---

## 21.3 Organizations, Teams, and Projects

```http
GET /api/v1/organizations
GET /api/v1/organizations/{id}
GET /api/v1/teams
GET /api/v1/teams/{id}
GET /api/v1/projects
GET /api/v1/projects/{id}
```

---

## 21.4 Metrics

```http
GET /api/v1/metrics
GET /api/v1/metrics/{metric_id}/values
```

---

## 21.5 Health Score

```http
GET /api/v1/health-score
```

---

## 21.6 Insights, Anomalies, Bottlenecks, and Risk

```http
GET /api/v1/insights
GET /api/v1/anomalies
GET /api/v1/bottlenecks
GET /api/v1/risks
GET /api/v1/risks/predictions
```

---

## 21.7 AI Explanations

```http
POST /api/v1/ai/explain
```

---

## 21.8 Simulator

The simulator is strictly an external data-generation service. It does not expose backend control APIs or config tables. It posts data directly to the raw ingestion API (`POST /api/v1/events`).

---

# 22. API Security

The API shall support:

- Authentication
- Authorization
- Request validation
- Rate limiting
- Audit logging

Provider credentials must never be accepted through arbitrary user-facing analytical requests.

---

# 23. Database Requirements

PostgreSQL shall contain logically separated schemas where appropriate.

Suggested structure:

```text
raw
canonical
analytics
configuration
audit
```

Example:

```text
raw.provider_events

canonical.teams
canonical.repositories
canonical.work_items
canonical.changes
canonical.reviews
canonical.builds
canonical.deployments
canonical.incidents
canonical.events

analytics.metrics
analytics.health_scores
analytics.anomalies
analytics.insights
analytics.ml_models
analytics.ml_features
analytics.risk_predictions
```

---

# 24. Database Indexing

Important indexes should include:

```text
provider + external_id
team_id + timestamp
repository_id + timestamp
event_type + timestamp
metric + team_id + timestamp
```

Indexes must be reviewed based on actual query patterns.

---

# 25. Data Retention

The system should support configurable retention policies.

Example:

```text
Raw events:
Long-term retention

Canonical events:
Long-term retention

Aggregated metrics:
Long-term retention

Temporary processing data:
Short-term retention
```

Deletion policies must not modify historical analytical results unexpectedly.

---

# 26. Data Consistency

The system shall preserve relationships between:

```text
Team
 ↓
Repository
 ↓
Change
 ↓
Review
 ↓
Build
 ↓
Deployment
 ↓
Incident
```

Where source systems provide these relationships.

Missing relationships must be represented as unknown rather than fabricated.

---

# 27. Error Handling

The system must distinguish:

```text
Validation Error
Authentication Error
Provider Error
Network Error
Database Error
Normalization Error
Analytics Error
AI Error
```

A failure in one subsystem must not unnecessarily cascade into unrelated subsystems.

For example:

```text
Cloud AI failure
      ↓
AI unavailable
      X
Core analytics
```

Core analytics must continue.

---

# 28. Observability

The platform shall expose:

### Application metrics

- Request count
- Request latency
- Error rate

### Ingestion metrics

- Events received
- Events processed
- Events rejected
- Duplicate events
- Processing latency

### Connector metrics

- Provider API status
- API failures
- Rate-limit events
- Last successful synchronization

### Analytics metrics

- Metric calculation duration
- Anomaly processing duration
- Health Score calculation duration

---

# 29. Logging

Structured logging should be used.

Example:

```json
{
  "timestamp": "2026-08-18T17:30:00Z",
  "service": "ingestion",
  "event_id": "evt_123",
  "provider": "github",
  "status": "processed"
}
```

Logs must not expose:

- API tokens
- Passwords
- Secrets
- Unnecessary personal information

---

# 30. Authentication and Authorization

The system should use:

```text
Authentication
     ↓
Identity
     ↓
Role
     ↓
Permission
     ↓
Resource
```

Suggested roles:

```text
ADMIN
ENGINEERING_LEADER
ENGINEERING_MANAGER
TECH_LEAD
ANALYST
DEVELOPER
```

Access must be scoped to appropriate organizations/teams.

---

# 31. Privacy Architecture

The privacy architecture should contain three distinct controls.

## Layer 1 — Data Minimization

Collect only data required for engineering analytics.

## Layer 2 — Access Control

Restrict sensitive data to authorized system components/users.

## Layer 3 — AI Sanitization

Prevent identity information from reaching external AI services.

---

# 32. Individual Productivity Prohibition

The analytics database must not contain a metric such as:

```text
developer_productivity_score
developer_performance_score
developer_rank
developer_efficiency_score
```

The architecture must not introduce such metrics indirectly.

Allowed examples:

```text
team_review_turnaround
team_deployment_frequency
team_cycle_time
team_change_failure_rate
```

Necessary individual operational information may still exist for technical integrity, attribution, authorization, and aggregation, subject to privacy/access controls.

---

# 33. Security Requirements

The system shall:

- Encrypt sensitive data in transit.
- Protect provider API credentials.
- Avoid hard-coded secrets.
- Implement RBAC.
- Log security-sensitive operations.
- Sanitize cloud AI payloads.
- Validate external input.
- Protect webhook endpoints.
- Apply rate limiting.
- Prevent unauthorized raw-data access.

---

# 34. Deployment Architecture

Recommended Docker Compose deployment:

```text
                 Nginx
                   │
                   ▼
              FastAPI API
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
   PostgreSQL    Redis     Worker
        │                     │
        └──────────┬──────────┘
                   ▼
             Analytics Engine
                   │
                   ▼
               Dashboard
```

Optional:

```text
FastAPI
   │
   ▼
Privacy Gateway
   │
   ▼
OpenRouter / Cloud LLM
```

---

# 35. Docker Services

Initial deployment may contain:

```text
codesense-api
codesense-worker
codesense-simulator
postgres
redis
codesense-dashboard
nginx
```

Not all services are mandatory for the first MVP.

---

# 36. Configuration Management

Configuration should be externalized.

Example:

```text
DATABASE_URL
REDIS_URL
API_SECRET
JWT_SECRET
OPENROUTER_API_KEY
LOG_LEVEL
ENVIRONMENT
```

Secrets must never be committed to Git.

---

# 37. Environment Separation

The project should support:

```text
development
testing
staging
production
```

The simulator should be disabled by default in production environments unless explicitly enabled.

---

# 38. Testing Requirements

## Unit Testing

Test:

- Event validation
- Normalization
- Metric formulas
- Health Score calculations
- Privacy filtering
- Anomaly detection

## Integration Testing

Test:

```text
Provider → Connector → Ingestion → Database
```

and:

```text
Simulator → Ingestion → Analytics → Dashboard
```

## Security Testing

Test:

- Unauthorized API access
- Invalid tokens
- Secret exposure
- AI identity leakage
- Raw-data access

## Performance Testing

Test:

- Event throughput
- API latency
- Database query performance
- Dashboard performance

---

# 39. Critical Test Cases

### Test 1 — Duplicate Event

Input:

```text
same provider + event ID
```

Expected:

```text
one analytical event
```

---

### Test 2 — Provider Mapping

Input:

```text
GitHub PR opened
GitLab MR created
```

Expected:

```text
both map to:
CHANGE_REVIEW_REQUESTED
```

---

### Test 3 — Privacy

Input:

```text
team metrics + developer identifiers
```

Expected cloud payload:

```text
team metrics only
```

---

### Test 4 — Offline Mode

Disable Internet.

Expected:

```text
ingestion → metrics → health score → dashboard
```

continues functioning where local data sources remain available.

Cloud AI:

```text
Unavailable
```

---

### Test 5 — Review Bottleneck

Inject:

```text
review delay ↑
review backlog ↑
```

Expected:

```text
REVIEW_BOTTLENECK
```

---

### Test 6 — Incident Spike

Inject:

```text
incident frequency ↑
MTTR ↑
```

Expected:

```text
Operational Health ↓
Health Score ↓
```

---

# 40. Performance Requirements

For the MVP, target:

| Requirement | Target |
|---|---:|
| API health response | < 200 ms |
| Normal API request | < 500 ms |
| Event ingestion acknowledgment | < 1 sec |
| Dashboard metric query | < 2 sec |
| Simulator-to-analytics latency | < 5 sec |
| Health Score recalculation | < 5 sec |

These are prototype targets and should be revised after load testing.

---

# 41. Scalability Requirements

The system should initially support at least:

```text
10 teams
50 repositories
100,000+ engineering events
```

without architectural changes.

The architecture should be capable of later scaling to:

```text
100+ teams
1,000+ repositories
millions of events
```

through:

- Horizontal workers
- Database indexing
- Batch processing
- Event queues
- Partitioning
- Caching

where necessary.

---

# 42. Frontend Technical Requirements

The dashboard shall communicate with the backend through REST APIs.

Required views:

```text
Overview
Delivery
Development Flow
CI/CD
Reliability
Insights
Anomalies
```

UI requirements:

- Responsive layout
- Interactive time-range selection
- Team selection
- Metric drill-down
- Score explanations
- Trend visualization
- Clear offline/AI availability state

---

# 43. Health Score UI Requirements

The dashboard must not display only:

```text
Health Score: 78
```

It should display:

```text
Engineering Health Score
78 / 100

Delivery Flow        82
Development Flow     80
Review Flow           71
CI/CD Reliability     85
Deployment Health     76
Operational Health    74
```

And provide evidence for significant changes.

---

# 44. Offline UI Requirements

When Internet connectivity is unavailable:

```text
● Core Analytics Available
● Historical Data Available
● Engineering Health Score Available
○ Cloud AI Unavailable
```

The application must not appear broken merely because cloud AI is unavailable.

---

# 45. AI Failure Handling

If an AI request fails:

```text
Analytics
   ↓
AI Request
   ↓
FAIL
   ↓
Fallback
```

Fallback options:

- Display structured analytical insight.
- Display metric-based explanation.
- Retry where appropriate.
- Show AI unavailable status.

Core analytics must never wait indefinitely for AI.

---

# 46. Data Flow Example

A simulated PR event:

```text
Simulator
   ↓
POST /api/v1/events
   ↓
Validation
   ↓
Raw Storage
   ↓
Canonicalization
   ↓
CHANGE_REVIEW_REQUESTED
   ↓
Review Analytics
   ↓
Review Turnaround
   ↓
Team Aggregation
   ↓
Engineering Health Score
   ↓
Dashboard
```

If AI explanation is requested:

```text
Team Aggregation
       ↓
Privacy Gateway
       ↓
Sanitized Payload
       ↓
LLM
       ↓
Explanation
```

---

# 47. Repository Structure

Recommended project structure:

```text
codesense/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── connectors/
│   │   ├── ingestion/
│   │   ├── models/
│   │   ├── normalization/
│   │   ├── metrics/
│   │   ├── health_score/
│   │   ├── anomaly_detection/
│   │   ├── ml/
│   │   ├── insights/
│   │   ├── privacy/
│   │   ├── ai/
│   │   ├── database/
│   │   └── core/
│   │
│   └── tests/
│
├── simulator/
│   ├── scenarios/
│   ├── generators/
│   ├── models/
│   └── tests/
│
├── frontend/
│   ├── components/
│   ├── pages/
│   ├── services/
│   └── charts/
│
├── docker/
│
├── docs/
│
├── scripts/
│
├── docker-compose.yml
├── .env.example
├── README.md
└── LICENSE
```

---

# 48. Development Phases

## Phase 1 — Foundation

Implement:

- Repository
- Docker
- PostgreSQL
- FastAPI
- Basic configuration
- Logging
- Health endpoint

---

## Phase 2 — Simulator

Implement:

- Entity generators
- Event generators
- Normal scenario
- Bottleneck scenarios
- Incident scenarios
- Event streaming

---

## Phase 3 — Ingestion

Implement:

- Event API
- Validation
- Idempotency
- Raw event storage

---

## Phase 4 — Canonical Layer

Implement:

- Canonical schema
- Event mapping
- Entity relationships
- Provider adapter interface

---

## Phase 5 — Analytics

Implement:

- Delivery metrics
- Review metrics
- CI/CD metrics
- Reliability metrics
- Historical aggregations

---

## Phase 6 — Engineering Health Score

Implement:

- Dimension scoring
- Weighting
- Normalization
- Score explanation
- Historical score

---

## Phase 7 — Intelligence

Implement:

- Bottleneck detection
- Anomaly detection
- Structured insights

---

## Phase 8 — Dashboard

Implement:

- Overview
- Delivery
- Development
- CI/CD
- Reliability
- Insights

---

## Phase 9 — AI

Implement:

- Privacy gateway
- Sanitized payload generation
- OpenRouter/cloud LLM integration
- AI explanations
- AI failure fallback

---

## Phase 10 — Real Provider Integration

After simulator-based validation:

```text
Simulator
   ↓
GitHub
   ↓
GitLab
   ↓
Jira
   ↓
CI/CD providers
```

The simulator remains available for testing.

---

# 49. MVP Technical Definition

The MVP is technically complete when this pipeline works end-to-end:

```text
                    ┌───────────────┐
                    │   Simulator   │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Ingestion API │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Raw Event DB  │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Normalization │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Canonical DB  │
                    └───────┬───────┘
                            │
                ┌───────────┼───────────┐
                ▼           ▼           ▼
             Metrics     Anomaly     Health
                │        Detection    Score
                └───────────┼───────────┘
                            ▼
                    ┌───────────────┐
                    │   Dashboard   │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Optional AI   │
                    └───────────────┘
```

---

# 50. Technical Acceptance Criteria

The implementation shall be considered technically successful when:

- [ ] Engineering events can be generated by the simulator.
- [ ] Events enter CodeSense through the ingestion API.
- [ ] Original provider events are preserved.
- [ ] Duplicate events are handled idempotently.
- [ ] Provider events are converted into canonical events.
- [ ] Canonical data can be queried independently of provider.
- [ ] Required engineering metrics are calculated.
- [ ] Team-level aggregation works.
- [ ] Engineering Health Score is calculated.
- [ ] Score components can be inspected.
- [ ] Review bottlenecks can be detected.
- [ ] CI/CD bottlenecks can be detected.
- [ ] Deployment/reliability issues can be detected.
- [ ] Historical trends are available.
- [ ] Individual productivity scoring is absent.
- [ ] Developer identity is removed before cloud AI requests.
- [ ] Core analytics operate without Internet connectivity.
- [ ] Cloud AI failure does not break analytics.
- [ ] Dashboard consumes backend APIs.
- [ ] At least one provider connector can be demonstrated.
- [ ] A second provider can theoretically be added through the connector interface without changing the metric engine.
- [ ] Automated tests cover critical processing and privacy paths.
- [ ] Docker-based deployment can reproduce the development environment.

---

# 51. Technical Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Provider API differences | High | Canonical adapter architecture |
| Inconsistent event schemas | High | Validation + normalization |
| Duplicate events | Medium | Idempotency keys |
| Large event volume | High | Queues + batching + indexing |
| Incorrect metrics | High | Deterministic metric engine + tests |
| Health Score oversimplification | High | Explainable multi-dimensional scoring |
| Privacy leakage | Critical | Privacy gateway + access controls |
| Cloud AI outage | Medium | AI optional + local fallback |
| Internet outage | Medium | Offline-first core analytics |
| Simulator unrealistic | Medium | Correlated event generation |
| Small-team deanonymization | High | Aggregation thresholds + RBAC |
| Provider lock-in | High | Canonical analytical layer |

---

# 52. Final Technical Architecture

The final technical architecture is based on six major layers:

```text
┌──────────────────────────────────────────────┐
│  1. SOURCE LAYER                            │
│  Git / Issues / CI/CD / Deployments /       │
│  Incidents / Simulator                      │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│  2. INGESTION LAYER                         │
│  Connectors / APIs / Webhooks / Validation  │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│  3. DATA LAYER                              │
│  Immutable Raw Events + Canonical Data      │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│  4. ANALYTICS LAYER                         │
│  Metrics + Trends + Health Score            │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│  5. INTELLIGENCE LAYER                      │
│  Bottlenecks + Anomalies + Insights         │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│  6. EXPERIENCE LAYER                        │
│  Dashboard + Reports + Optional AI          │
└──────────────────────────────────────────────┘
```

---

# 53. Final Technical Constraints

The following constraints are **architecturally locked**:

### Constraint 1 — No Individual Productivity Scores

CodeSense must not calculate, store, rank, or display individual developer productivity scores.

### Constraint 2 — No Developer Identity to Cloud AI

Developer identity must be removed before any cloud LLM request.

### Constraint 3 — Raw Events Are Immutable

Provider events are preserved exactly as received.

### Constraint 4 — Canonical Analytics

All cross-provider analytics must operate on the canonical analytical layer.

### Constraint 5 — Offline Core

Loss of Internet connectivity must not disable:

- Raw/local data processing
- Canonicalization
- Metrics
- Engineering Health Score
- Historical analytics
- Dashboards

### Constraint 6 — AI Is Optional

Cloud AI must never be a hard dependency of CodeSense.

### Constraint 7 — Provider Agnostic

Adding or replacing a provider must not require rewriting the analytics engine.

### Constraint 8 — Team-Level Intelligence

The primary analytical unit is the **team**, not the individual developer.

### Constraint 9 — Simulator Separation

The simulator exists only to generate realistic engineering data. It must use the same ingestion interfaces as real data sources.

### Constraint 10 — Explainability

Every major analytical result, especially Engineering Health Score changes and detected bottlenecks, must have traceable metric evidence.

---

# 54. Final Technical Definition

**CodeSense is technically defined as a modular, provider-agnostic engineering analytics system consisting of:**

```text
Provider Connectors
        +
Real-Time Simulator
        +
Event Ingestion
        +
Immutable Raw Storage
        +
Canonical Event/Data Layer
        +
Metric Engine
        +
Engineering Health Score
        +
Trend Engine
        +
Bottleneck Detection
        +
Anomaly Detection
        +
Privacy Gateway
        +
Optional AI Layer
        +
REST API
        +
Engineering Analytics Dashboard
```

The fundamental data flow is:

```text
Engineering Activity
        ↓
Provider / Simulator
        ↓
Ingestion
        ↓
Immutable Raw Events
        ↓
Canonicalization
        ↓
Canonical Analytical Layer
        ↓
Team-Level Metrics
        ↓
Engineering Health Score
        ↓
Bottleneck / Anomaly Detection
        ↓
Insights
        ↓
Dashboard
        ↓
Optional Privacy-Safe AI Explanation
```

The architecture therefore separates **data collection, data preservation, normalization, analytics, intelligence, privacy, and presentation**, allowing CodeSense to scale from the academic prototype into a production-oriented engineering intelligence platform without violating its core privacy and provider-agnostic requirements.