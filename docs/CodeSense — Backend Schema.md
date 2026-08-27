# CodeSense — Backend Schema

**Version:** 1.0  
**Date:** August 18, 2026  
**Database:** PostgreSQL  
**Backend:** Python + FastAPI  
**Architecture:** Raw → Canonical → Analytics

---

# 1. Database Architecture

```text
PostgreSQL
│
├── raw
│   └── provider_events
│
├── core
│   ├── organizations
│   ├── teams
│   ├── repositories
│   ├── projects
│   ├── work_items
│   ├── changes
│   ├── reviews
│   ├── builds
│   ├── deployments
│   ├── incidents
│   └── canonical_events
│
├── analytics
│   ├── metric_definitions
│   ├── metric_values
│   ├── health_scores
│   ├── health_score_components
│   ├── engineering_trends
│   ├── analytics_snapshots
│   ├── ai_insights
│   └── ai_insight_requests
│
├── configuration
│   ├── providers
│   ├── connector_configs
│   └── health_score_configs
│
└── audit
    └── audit_logs
```

---

# 2. Core Architecture

```text
Provider / Simulator
        ↓
Ingestion
        ↓
Raw Event Store
        ↓
Normalization
        ↓
Canonical Data Layer
        ↓
Analytics Engine
        ↓
Health Score / Anomalies / Bottlenecks
        ↓
Insights
        ↓
API
        ↓
Dashboard / Optional AI
```

---

# 3. `raw` Schema

## 3.1 `raw.provider_events`

Stores the original provider event exactly as received.

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Internal event ID |
| provider | VARCHAR(100) | NOT NULL | Source provider |
| external_event_id | VARCHAR(255) | NOT NULL | Provider event ID |
| event_type | VARCHAR(255) | NOT NULL | Provider event type |
| received_at | TIMESTAMPTZ | NOT NULL | CodeSense receipt time |
| event_timestamp | TIMESTAMPTZ | | Original event time |
| payload | JSONB | NOT NULL | Original untouched payload |
| payload_hash | VARCHAR(128) | | Integrity/deduplication hash |
| source | VARCHAR(50) | NOT NULL | API/webhook/simulator/batch |
| processing_status | VARCHAR(50) | NOT NULL | Processing state |
| created_at | TIMESTAMPTZ | NOT NULL | Database timestamp |

### Rules

- `payload` must remain immutable.
- Raw provider data must not be transformed in-place.
- Duplicate events must be detected.
- Original provider information must remain recoverable.

### Unique Constraint

```text
UNIQUE(provider, external_event_id)
```

---

# 4. `core` Schema

The `core` schema contains the provider-independent representation of engineering activity.

---

## 4.1 `core.organizations`

```text
id
name
external_id
created_at
updated_at
```

### Relationships

```text
organization
     │
     └── 1:N ── teams
```

---

## 4.2 `core.teams`

```text
id
organization_id
name
external_id
status
created_at
updated_at
```

### Relationships

```text
organization
     │
     └── teams
          ├── repositories
          ├── projects
          ├── work_items
          └── incidents
```

---

## 4.3 `core.repositories`

```text
id
team_id
provider
external_id
name
url
default_branch
is_active
created_at
updated_at
```

### Constraint

```text
UNIQUE(provider, external_id)
```

---

## 4.4 `core.projects`

Used for Jira, Linear, or similar project-management systems.

```text
id
team_id
provider
external_id
name
description
status
created_at
updated_at
```

---

## 4.5 `core.work_items`

Represents issues, tasks, stories, bugs, etc.

```text
id
team_id
project_id
repository_id
provider
external_id
item_type
title
status
priority
created_at
started_at
completed_at
updated_at
```

### Example item types

```text
BUG
FEATURE
TASK
STORY
INCIDENT
```

---

## 4.6 `core.changes`

Canonical representation of Pull Requests, Merge Requests, and similar code changes.

```text
id
team_id
repository_id
work_item_id
provider
external_id
title
status
created_at
updated_at
merged_at
closed_at
additions
deletions
changed_files
```

### Provider mapping

```text
GitHub Pull Request
        ↓
core.changes

GitLab Merge Request
        ↓
core.changes
```

---

## 4.7 `core.reviews`

Represents code-review activity.

```text
id
change_id
provider
external_id
status
requested_at
started_at
completed_at
created_at
updated_at
```

### Possible statuses

```text
PENDING
APPROVED
CHANGES_REQUESTED
DISMISSED
COMPLETED
```

### Privacy Rule

CodeSense may retain necessary reviewer references internally for event processing, authorization, or aggregation, but must not generate individual productivity scores.

---

## 4.8 `core.builds`

Represents CI/build executions.

```text
id
team_id
repository_id
change_id
provider
external_id
status
started_at
completed_at
duration_seconds
branch
commit_sha
created_at
```

### Possible statuses

```text
RUNNING
SUCCESS
FAILED
CANCELLED
```

---

## 4.9 `core.deployments`

Represents deployment activity.

```text
id
team_id
repository_id
change_id
provider
external_id
environment
status
started_at
completed_at
duration_seconds
version
created_at
```

### Environments

```text
DEVELOPMENT
STAGING
PRODUCTION
```

### Statuses

```text
SUCCESS
FAILED
ROLLED_BACK
CANCELLED
```

---

## 4.10 `core.incidents`

Represents operational incidents.

```text
id
team_id
repository_id
provider
external_id
title
severity
status
created_at
acknowledged_at
resolved_at
updated_at
```

### Severity

```text
SEV1
SEV2
SEV3
SEV4
```

### Status

```text
OPEN
ACKNOWLEDGED
RESOLVED
CLOSED
```

---

# 5. `core.canonical_events`

This is the central cross-provider analytical event layer.

```text
id
raw_event_id
team_id
repository_id
project_id
event_type
event_timestamp
actor_ref
entity_type
entity_id
metadata
created_at
```

---

## 5.1 Canonical Event Types

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
BUILD_SUCCEEDED
BUILD_FAILED

DEPLOYMENT_STARTED
DEPLOYMENT_COMPLETED
DEPLOYMENT_FAILED
DEPLOYMENT_ROLLED_BACK

INCIDENT_CREATED
INCIDENT_ACKNOWLEDGED
INCIDENT_RESOLVED
```

---

# 6. Actor Identity Model

The canonical event may contain:

```text
actor_ref
```

when technically required for:

- Event integrity
- Event correlation
- Authorization
- Internal aggregation
- Audit purposes

However:

```text
actor_ref
      ↓
Privacy Filter
      ↓
REMOVED
      ↓
Cloud AI
```

### Prohibited

CodeSense must not create:

```text
developer_productivity_score
developer_performance_score
developer_rank
developer_efficiency_score
```

### Allowed

```text
team_review_turnaround
team_deployment_frequency
team_cycle_time
team_change_failure_rate
```

---

# 7. `analytics` Schema

The `analytics` schema contains derived engineering intelligence.

---

## 7.1 `analytics.metric_definitions`

```text
id
metric_key
name
description
category
unit
aggregation_method
is_active
created_at
updated_at
```

### Initial Metrics

```text
deployment_frequency
lead_time
cycle_time
review_turnaround
review_backlog
build_success_rate
pipeline_duration
deployment_failure_rate
change_failure_rate
mttr
work_in_progress
```

---

# 8. `analytics.metric_values`

Stores calculated metric values over time.

```text
id
metric_id
team_id
repository_id
period_start
period_end
value
baseline_value
change_percentage
calculated_at
```

### Example

```text
Team:
Platform Team

Metric:
review_turnaround

Current:
9.4 hours

Baseline:
7.1 hours

Change:
+32.4%
```

---

# 9. `analytics.health_scores`

Stores the Engineering Health Score.

```text
id
team_id
period_start
period_end
score
previous_score
score_change
calculated_at
```

### Example

```text
Team:
Platform Team

Score:
78

Previous Score:
83

Change:
-5
```

---

# 10. `analytics.health_score_components`

Stores the individual dimensions contributing to the Engineering Health Score.

```text
id
health_score_id
dimension
score
weight
contribution
```

### Initial Dimensions

```text
delivery_flow
development_flow
review_flow
cicd_reliability
deployment_health
operational_health
```

### Example

```text
Engineering Health Score
│
├── Delivery Flow       82
├── Development Flow    80
├── Review Flow         71
├── CI/CD Reliability   85
├── Deployment Health   76
└── Operational Health  74
```

---

# 11. `analytics.analytics_snapshots`

Stores precomputed analytical summaries.

```text
id
organization_id
project_id
team_id
snapshot_date
metrics (JSONB)
generated_at
```

---

# 12. `analytics.engineering_trends`

Stores detected trends and statistical changes.

```text
id
organization_id
project_id
team_id
metric_id
trend_type
magnitude
confidence
detected_at
metadata (JSONB)
```

### Trend Types

```text
IMPROVING
DECLINING
STABLE
ANOMALY
```

---

# 13. `analytics.ai_insight_requests` and `analytics.ai_insights`

Tracks requests sent through the AI Gateway and stores AI-generated insights.

### `analytics.ai_insight_requests`

```text
id
organization_id
project_id
requested_by
model_provider
model_name
request_type
sanitized_context (JSONB)
status (COMPLETED/FAILED)
created_at
completed_at
```

### `analytics.ai_insights`

```text
id
request_id
organization_id
project_id
insight_type
title
content
confidence
source_metrics (JSONB)
status
created_at
```

---

# 14. `configuration` Schema

---

## 14.1 `configuration.providers`

```text
id
name
provider_type
status
created_at
updated_at
```

### Example providers

```text
GitHub
GitLab
Jira
Jenkins
Simulator
```

---

## 14.2 `configuration.connector_configs`

```text
id
provider_id
organization_id
config
is_enabled
last_sync_at
created_at
updated_at
```

### Security Rule

Provider credentials/API keys should not be stored as plain text in this table.

Use:

```text
Environment Variables
        OR
Secrets Manager
```

---

## 14.3 `configuration.health_score_configs`

```text
id
organization_id
dimension
weight
minimum_threshold
maximum_threshold
is_enabled
created_at
updated_at
```

### Initial configuration

```text
Delivery Flow       20%
Development Flow    20%
Review Flow         15%
CI/CD Reliability   15%
Deployment Health   15%
Operational Health  15%
```

---

---

# 15. `audit` Schema

## 15.1 `audit.audit_logs`

```text
id
actor_reference
action
resource_type
resource_id
timestamp
ip_address
metadata
```

### Example actions

```text
TEAM_VIEWED
RAW_EVENT_ACCESSED
CONNECTOR_CREATED
CONNECTOR_DISABLED
HEALTH_CONFIG_UPDATED
AI_REQUEST_CREATED
```

---

# 16. Complete Relationship Model

```text
                         organizations
                              │
                              ▼
                            teams
                       ┌──────┼──────┐
                       │      │      │
                       ▼      ▼      ▼
                 repositories projects incidents
                       │          │
                       │          ▼
                       │      work_items
                       │
                       ▼
                    changes
                       │
                  ┌────┴────┐
                  ▼         ▼
               reviews    builds
                              │
                              ▼
                         deployments


raw.provider_events
        │
        ▼
core.canonical_events
        │
        ├───────────────┐
        ▼               ▼
metric_values       anomalies
        │
        ├───────────────┐
        ▼               ▼
health_scores       bottlenecks
        │
        ▼
health_score_components
        │
        ▼
insights
```

---

# 17. Backend Event Processing Flow

```text
Provider / Simulator
        │
        ▼
┌──────────────────┐
│ Ingestion API    │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Validate Event   │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Deduplicate      │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Raw Event Store  │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Normalization    │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Canonical Events │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Metric Engine    │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Health Score     │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Trend & Snapshot │
│ Engine           │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Insight Engine   │
└────────┬─────────┘
         ▼
       API
         │
         ▼
    Dashboard
```

---

# 18. API-to-Database Mapping

| API | Primary Tables |
|---|---|
| `POST /events` | `raw.provider_events` |
| `POST /events/batch` | `raw.provider_events` |
| `GET /organizations` | `core.organizations` |
| `GET /teams` | `core.teams` |
| `GET /projects` | `core.projects` |
| `GET /repositories` | `core.repositories` |
| `GET /metrics` | `analytics.metric_definitions` |
| `GET /metrics/{id}/values` | `analytics.metric_values` |
| `GET /health-score` | `analytics.health_scores` |
| `GET /insights` | `analytics.ai_insights` |
| `POST /ai/explain` | `analytics.ai_insight_requests` / `analytics.ai_insights` |

---

# 19. Essential Indexes

```sql
CREATE INDEX idx_raw_events_timestamp
ON raw.provider_events(event_timestamp);

CREATE INDEX idx_raw_events_provider
ON raw.provider_events(provider);

CREATE INDEX idx_canonical_events_org_team_project_time
ON core.canonical_events(organization_id, team_id, project_id, occurred_at);

CREATE INDEX idx_canonical_events_repo_time
ON core.canonical_events(repository_id, occurred_at);

CREATE INDEX idx_canonical_events_type_time
ON core.canonical_events(event_type, occurred_at);

CREATE INDEX idx_metric_values_org_team_project_period
ON analytics.metric_values(organization_id, team_id, project_id, period_start, period_end);

CREATE INDEX idx_health_scores_org_team_project_period
ON analytics.health_scores(organization_id, team_id, project_id, period_start, period_end);

CREATE INDEX idx_engineering_trends_org_team_project_time
ON analytics.engineering_trends(organization_id, team_id, project_id, detected_at);
```

---

# 20. Core PostgreSQL DDL

## 20.1 Schema Creation

```sql
CREATE SCHEMA raw;
CREATE SCHEMA core;
CREATE SCHEMA analytics;
CREATE SCHEMA configuration;
CREATE SCHEMA audit;
```

---

## 20.2 Organizations and Teams

```sql
CREATE TABLE core.organizations (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    external_id VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE core.teams (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL
        REFERENCES core.organizations(id),
    name VARCHAR(255) NOT NULL,
    external_id VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 20.3 Repositories

```sql
CREATE TABLE core.repositories (
    id UUID PRIMARY KEY,
    team_id UUID NOT NULL
        REFERENCES core.teams(id),
    provider VARCHAR(100) NOT NULL,
    external_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    url TEXT,
    default_branch VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(provider, external_id)
);
```

---

## 20.4 Raw Events

```sql
CREATE TABLE raw.provider_events (
    id UUID PRIMARY KEY,
    provider VARCHAR(100) NOT NULL,
    external_event_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(255) NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_timestamp TIMESTAMPTZ,
    payload JSONB NOT NULL,
    payload_hash VARCHAR(128),
    source VARCHAR(50) NOT NULL,
    processing_status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(provider, external_event_id)
);
```

---

## 20.5 Canonical Events

```sql
CREATE TABLE core.canonical_events (
    id UUID PRIMARY KEY,

    raw_event_id UUID NOT NULL
        REFERENCES raw.provider_events(id),

    organization_id UUID NOT NULL
        REFERENCES core.organizations(id),

    team_id UUID
        REFERENCES core.teams(id),

    project_id UUID NOT NULL
        REFERENCES core.projects(id),

    repository_id UUID
        REFERENCES core.repositories(id),

    event_type VARCHAR(100) NOT NULL,

    occurred_at TIMESTAMPTZ NOT NULL,

    actor_ref VARCHAR(255),

    entity_type VARCHAR(100),

    entity_id UUID,

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 20.6 Changes

```sql
CREATE TABLE core.changes (
    id UUID PRIMARY KEY,

    team_id UUID NOT NULL
        REFERENCES core.teams(id),

    repository_id UUID NOT NULL
        REFERENCES core.repositories(id),

    provider VARCHAR(100) NOT NULL,

    external_id VARCHAR(255) NOT NULL,

    title TEXT,

    status VARCHAR(50),

    created_at TIMESTAMPTZ,

    updated_at TIMESTAMPTZ,

    merged_at TIMESTAMPTZ,

    closed_at TIMESTAMPTZ,

    additions INTEGER DEFAULT 0,

    deletions INTEGER DEFAULT 0,

    changed_files INTEGER DEFAULT 0,

    UNIQUE(provider, external_id)
);
```

---

## 20.7 Reviews

```sql
CREATE TABLE core.reviews (
    id UUID PRIMARY KEY,

    change_id UUID NOT NULL
        REFERENCES core.changes(id),

    provider VARCHAR(100) NOT NULL,

    external_id VARCHAR(255),

    status VARCHAR(50),

    requested_at TIMESTAMPTZ,

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 20.8 Builds

```sql
CREATE TABLE core.builds (
    id UUID PRIMARY KEY,

    team_id UUID NOT NULL
        REFERENCES core.teams(id),

    repository_id UUID NOT NULL
        REFERENCES core.repositories(id),

    change_id UUID
        REFERENCES core.changes(id),

    provider VARCHAR(100) NOT NULL,

    external_id VARCHAR(255) NOT NULL,

    status VARCHAR(50),

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    duration_seconds INTEGER,

    branch VARCHAR(255),

    commit_sha VARCHAR(255),

    UNIQUE(provider, external_id)
);
```

---

## 20.9 Deployments

```sql
CREATE TABLE core.deployments (
    id UUID PRIMARY KEY,

    team_id UUID NOT NULL
        REFERENCES core.teams(id),

    repository_id UUID
        REFERENCES core.repositories(id),

    change_id UUID
        REFERENCES core.changes(id),

    provider VARCHAR(100) NOT NULL,

    external_id VARCHAR(255) NOT NULL,

    environment VARCHAR(100),

    status VARCHAR(50),

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    duration_seconds INTEGER,

    version VARCHAR(255),

    UNIQUE(provider, external_id)
);
```

---

# 21. Analytics DDL

```sql
CREATE TABLE analytics.metric_definitions (
    id UUID PRIMARY KEY,

    metric_key VARCHAR(100) UNIQUE NOT NULL,

    name VARCHAR(255) NOT NULL,

    description TEXT,

    category VARCHAR(100),

    unit VARCHAR(50),

    aggregation_method VARCHAR(50),

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

```sql
CREATE TABLE analytics.metric_values (
    id UUID PRIMARY KEY,

    metric_id UUID NOT NULL
        REFERENCES analytics.metric_definitions(id),

    team_id UUID NOT NULL
        REFERENCES core.teams(id),

    repository_id UUID
        REFERENCES core.repositories(id),

    period_start TIMESTAMPTZ NOT NULL,

    period_end TIMESTAMPTZ NOT NULL,

    value DOUBLE PRECISION NOT NULL,

    baseline_value DOUBLE PRECISION,

    change_percentage DOUBLE PRECISION,

    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

```sql
CREATE TABLE analytics.health_scores (
    id UUID PRIMARY KEY,

    team_id UUID NOT NULL
        REFERENCES core.teams(id),

    period_start TIMESTAMPTZ NOT NULL,

    period_end TIMESTAMPTZ NOT NULL,

    score DOUBLE PRECISION NOT NULL,

    previous_score DOUBLE PRECISION,

    score_change DOUBLE PRECISION,

    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

```sql
CREATE TABLE analytics.health_score_components (
    id UUID PRIMARY KEY,

    health_score_id UUID NOT NULL
        REFERENCES analytics.health_scores(id)
        ON DELETE CASCADE,

    dimension VARCHAR(100) NOT NULL,

    score DOUBLE PRECISION NOT NULL,

    weight DOUBLE PRECISION NOT NULL,

    contribution DOUBLE PRECISION NOT NULL
);
```

---

# 22. Analytics Snapshots / Trends / AI Insights DDL

```sql
CREATE TABLE analytics.analytics_snapshots (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES core.organizations(id),
    project_id UUID NOT NULL REFERENCES core.projects(id),
    team_id UUID NOT NULL REFERENCES core.teams(id),
    snapshot_date DATE NOT NULL,
    metrics JSONB NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

```sql
CREATE TABLE analytics.engineering_trends (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES core.organizations(id),
    project_id UUID NOT NULL REFERENCES core.projects(id),
    team_id UUID NOT NULL REFERENCES core.teams(id),
    metric_id UUID NOT NULL REFERENCES analytics.metric_definitions(id),
    trend_type VARCHAR(50) NOT NULL,
    magnitude DOUBLE PRECISION,
    confidence DOUBLE PRECISION,
    detected_at TIMESTAMPTZ NOT NULL,
    metadata JSONB DEFAULT '{}'
);
```

```sql
CREATE TABLE analytics.ml_features (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES core.organizations(id),
    team_id UUID REFERENCES core.teams(id),
    target_entity_type VARCHAR(50) NOT NULL,
    target_entity_id UUID NOT NULL,
    feature_vector JSONB NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE configuration.model_registry (
    id UUID PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    version VARCHAR(50) NOT NULL,
    scope VARCHAR(50) NOT NULL, -- GLOBAL, ORG, TEAM
    organization_id UUID REFERENCES core.organizations(id),
    team_id UUID REFERENCES core.teams(id),
    artifact_path TEXT NOT NULL,
    status VARCHAR(30) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE analytics.ml_predictions (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES core.organizations(id),
    model_id UUID NOT NULL REFERENCES configuration.model_registry(id),
    prediction_type VARCHAR(50) NOT NULL,
    target_entity_id UUID NOT NULL,
    score DOUBLE PRECISION NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    evidence JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE analytics.training_jobs (
    id UUID PRIMARY KEY,
    model_registry_id UUID NOT NULL REFERENCES configuration.model_registry(id),
    status VARCHAR(30) NOT NULL,
    metrics JSONB,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);
```

```sql
CREATE TABLE analytics.ai_insight_requests (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES core.organizations(id),
    project_id UUID NOT NULL REFERENCES core.projects(id),
    requested_by UUID NOT NULL REFERENCES core.users(id),
    model_provider VARCHAR(100) NOT NULL,
    model_name VARCHAR(150) NOT NULL,
    request_type VARCHAR(100) NOT NULL,
    sanitized_context JSONB NOT NULL,
    status VARCHAR(30) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
```

```sql
CREATE TABLE analytics.ai_insights (
    id UUID PRIMARY KEY,
    request_id UUID REFERENCES analytics.ai_insight_requests(id),
    organization_id UUID NOT NULL REFERENCES core.organizations(id),
    project_id UUID NOT NULL REFERENCES core.projects(id),
    insight_type VARCHAR(100) NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    confidence DOUBLE PRECISION,
    source_metrics JSONB DEFAULT '{}',
    status VARCHAR(30) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

# 23. Privacy Architecture

```text
                    Raw Events
                        │
                        ▼
                Canonical Events
                        │
                        ▼
                 Team Analytics
                        │
                        ▼
                Privacy Gateway
                        │
             ┌──────────┴──────────┐
             │                     │
       Identity Present       Identity Removed
             │                     │
             X                     ▼
        Cloud AI              Cloud AI
        BLOCKED                ALLOWED
```

### Cloud AI may receive

```text
Team metrics
Aggregated trends
Health Score
Anomaly information
Bottleneck information
Non-identifying context
```

### Cloud AI must not receive

```text
Developer name
Developer email
Developer username
Developer ID
Raw provider payload
Individual productivity metrics
Personal access tokens
```

---

# 24. Offline Architecture

```text
                    CodeSense
                        │
            ┌───────────┴───────────┐
            │                       │
            ▼                       ▼
      Core Analytics            Cloud AI
            │                       │
            │                 Internet Required
            │                       │
            ▼                       ▼
        WORKS                    OPTIONAL
        OFFLINE
```

When Internet connectivity is lost:

```text
Raw Storage             ✓
Canonicalization        ✓
Metrics                 ✓
Health Score            ✓
Historical Analytics    ✓
Dashboard               ✓
Cloud AI                ✗
```

---

# 25. Simulator Integration

The simulator must use the same ingestion pipeline as real providers.

```text
Simulator
    │
    ▼
POST /api/v1/events
    │
    ▼
Raw Event Store
    │
    ▼
Normalization
    │
    ▼
Canonical Layer
    │
    ▼
Analytics
```

The simulator must **not directly insert analytical results**.

This ensures that the simulator actually tests the CodeSense backend.

---

# 26. MVP Tables

For the first working implementation, prioritize these tables:

```text
RAW
────
raw.provider_events

CORE
────
core.organizations
core.teams
core.repositories
core.changes
core.reviews
core.builds
core.deployments
core.canonical_events

ANALYTICS
─────────
analytics.metric_definitions
analytics.metric_values
analytics.health_scores
analytics.health_score_components
analytics.anomalies
analytics.bottlenecks
analytics.insights
```

Add these later:

```text
core.projects
core.work_items
core.incidents

configuration.*
audit.*
```

---

# 27. Final Schema Principle

The CodeSense backend follows this rule:

```text
                    RAW
                     │
             Source of Truth
                     │
                     ▼
                 CANONICAL
                     │
            Provider Independent
                     │
                     ▼
                ANALYTICS
                     │
              Derived Metrics
                     │
                     ▼
               INTELLIGENCE
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
     Health       Hybrid ML    Fusion Engine
      Score         Engine    (Rules+Stats+ML)
        │            │            │
        └────────────┼────────────┘
                     ▼
                  Insights
                     │
              ┌──────┴──────┐
              ▼             ▼
          Dashboard       AI
```

## Core design decisions

1. **`raw.provider_events` is immutable.**
2. **`core.canonical_events` is the provider-independent event layer.**
3. **`analytics.*` contains derived engineering intelligence.**
4. **The primary analytical unit is the team.**
5. **Individual productivity scoring does not exist.**
6. **Developer identity is never sent to cloud LLMs.**
7. **Core analytics work without Internet connectivity.**
8. **The simulator uses the same ingestion pipeline as real providers.**
9. **Provider-specific logic remains inside connectors/adapters.**
10. **Every Health Score and insight should be traceable to underlying metrics.**