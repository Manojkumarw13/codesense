# CodeSense — Database Schema

**Document Status:** Draft / Editable  
**Version:** 1.0  
**Project:** CodeSense  
**Database:** PostgreSQL  
**ORM:** SQLAlchemy  
**Purpose:** Define the persistent data model for CodeSense

---

# 1. Database Objectives

The CodeSense database must support:

- User authentication and authorization
- Organizations and teams
- Projects and repositories
- External provider integrations
- Immutable raw provider events
- Canonical engineering events
- Engineering metrics
- Aggregated analytics
- Engineering Health Score
- AI-generated insights
- Audit logging
- System configuration
- Offline operation

The database must preserve the separation between:

```text
Raw Provider Data
        ↓
Canonical Data
        ↓
Analytics
        ↓
Engineering Health
        ↓
AI Insights
```

---

# 2. Core Database Principles

## 2.1 Raw events are immutable

Raw provider events must never be overwritten by the canonical transformation process.

## 2.2 Canonical data is provider-independent

Analytics should primarily operate on canonical events and analytical tables.

## 2.3 No individual productivity scores

The schema must not contain a table or field whose purpose is to calculate or store individual developer productivity scores.

## 2.4 Privacy-aware identity handling

Developer identity may be stored where required for legitimate application functionality, authorization, attribution, or operational metrics.

However:

```text
Developer Identity
        X
        ↓
Cloud LLM
```

Identity must be removed before cloud-AI requests.

## 2.5 Database is the source of truth

Caches, dashboards, queues, and AI systems must not become authoritative data stores.

---

# 3. High-Level Entity Relationship

```text
Organization
     │
     ├────────────── Users
     │
     ├────────────── Teams
     │                    │
     │                    └──── Team Members
     │
     ├────────────── Projects
     │                    │
     │                    ├──── Repositories
     │                    │
     │                    └──── Provider Connections
     │
     └────────────── Settings


Provider Connection
        │
        ▼
Raw Provider Events
        │
        ▼
Canonical Events
        │
        ├────────────── Metrics
        │
        └────────────── Analytics
                           │
                           ▼
                  Engineering Health
                           │
                           ▼
                      AI Insights


All important actions
        │
        ▼
    Audit Logs
```

---

# 4. Database Schema Overview

Recommended schema groups:

```text
Identity
├── organizations
├── users
├── roles
├── permissions
├── user_roles
└── teams

Project
├── projects
├── repositories
└── project_members

Integration
├── providers
├── provider_connections
└── webhook_subscriptions

Raw Data
└── raw_provider_events

Canonical Data
├── canonical_events
├── commits
├── pull_requests
├── reviews
├── issues
└── deployments

Analytics
├── metric_definitions
├── metric_values
├── analytics_snapshots
├── engineering_health_scores
└── engineering_trends

AI
├── ai_insight_requests
└── ai_insights

System
├── audit_logs
├── system_settings
└── data_processing_jobs
```

---

# 5. Identity Tables

## 5.1 organizations

Represents the top-level tenant or engineering organization.

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Organization ID |
| name | VARCHAR(255) | NOT NULL | Organization name |
| slug | VARCHAR(100) | UNIQUE, NOT NULL | URL-safe identifier |
| status | VARCHAR(30) | NOT NULL | Active/inactive |
| created_at | TIMESTAMPTZ | NOT NULL | Creation time |
| updated_at | TIMESTAMPTZ | NOT NULL | Last update |

---

# 6. users

Stores application users.

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | User ID |
| organization_id | UUID | FK | Organization |
| email | VARCHAR(320) | UNIQUE | Login email |
| display_name | VARCHAR(255) | | Display name |
| password_hash | TEXT | | Password hash |
| status | VARCHAR(30) | NOT NULL | Account status |
| last_login_at | TIMESTAMPTZ | | Last login |
| created_at | TIMESTAMPTZ | NOT NULL | Creation time |
| updated_at | TIMESTAMPTZ | NOT NULL | Last update |

Passwords must never be stored in plaintext.

---

# 7. roles

Defines application roles.

Example roles:

```text
ADMIN
ENGINEERING_LEADER
ENGINEERING_MANAGER
TECH_LEAD
ANALYST
DEVELOPER
```

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| name | VARCHAR(100) | UNIQUE |
| description | TEXT | |
| created_at | TIMESTAMPTZ | |

---

# 8. permissions

Defines granular permissions.

Examples:

```text
project.read
project.write
analytics.read
analytics.export
provider.manage
user.manage
audit.read
configuration.manage
```

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| name | VARCHAR(150) | UNIQUE |
| description | TEXT | |

---

# 9. user_roles

Many-to-many relationship between users and roles.

| Column | Type | Constraints |
|---|---|---|
| user_id | UUID | FK |
| role_id | UUID | FK |
| assigned_at | TIMESTAMPTZ | |
| assigned_by | UUID | FK |

Primary key:

```text
(user_id, role_id)
```

---

# 10. teams

Represents engineering teams.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| organization_id | UUID | FK |
| name | VARCHAR(255) | NOT NULL |
| description | TEXT | |
| status | VARCHAR(30) | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

---

# 11. team_members

Associates users with teams.

| Column | Type | Constraints |
|---|---|---|
| team_id | UUID | FK |
| user_id | UUID | FK |
| role | VARCHAR(50) | |
| joined_at | TIMESTAMPTZ | |

Primary key:

```text
(team_id, user_id)
```

---

# 12. Project Tables

## 12.1 projects

Represents an engineering project.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| organization_id | UUID | FK |
| name | VARCHAR(255) | NOT NULL |
| key | VARCHAR(50) | UNIQUE within organization |
| description | TEXT | |
| status | VARCHAR(30) | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

---

# 13. project_members

Controls project-level access.

| Column | Type | Constraints |
|---|---|---|
| project_id | UUID | FK |
| user_id | UUID | FK |
| access_level | VARCHAR(50) | |
| created_at | TIMESTAMPTZ | |

Example access levels:

```text
OWNER
MAINTAINER
CONTRIBUTOR
VIEWER
```

---

# 14. repositories

Represents source-code repositories.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | FK |
| provider_connection_id | UUID | FK |
| external_id | VARCHAR(255) | |
| name | VARCHAR(255) | |
| full_name | VARCHAR(500) | |
| url | TEXT | |
| default_branch | VARCHAR(255) | |
| language | VARCHAR(100) | |
| status | VARCHAR(30) | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

Recommended unique constraint:

```text
(provider_connection_id, external_id)
```

---

# 15. Integration Tables

## 15.1 providers

Defines supported external platforms.

Example:

```text
GitHub
GitLab
Jira
CI/CD provider
```

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| name | VARCHAR(100) | UNIQUE |
| provider_type | VARCHAR(50) | |
| version | VARCHAR(50) | |
| status | VARCHAR(30) | |
| created_at | TIMESTAMPTZ | |

---

# 16. provider_connections

Represents a configured connection to an external platform.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| organization_id | UUID | FK |
| provider_id | UUID | FK |
| name | VARCHAR(255) | |
| base_url | TEXT | |
| credential_reference | TEXT | |
| status | VARCHAR(30) | |
| last_sync_at | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

Credentials should be stored using a secure secrets-management mechanism.

The database should store only a reference where possible.

---

# 17. webhook_subscriptions

Stores provider webhook configuration.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| provider_connection_id | UUID | FK |
| external_subscription_id | VARCHAR(255) | |
| event_types | JSONB | |
| status | VARCHAR(30) | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

---

# 18. Raw Provider Event Storage

## 18.1 raw_provider_events

This is one of the most important tables in CodeSense.

It stores the original provider event.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| provider_connection_id | UUID | FK |
| provider_event_id | VARCHAR(255) | |
| event_type | VARCHAR(150) | |
| received_at | TIMESTAMPTZ | |
| payload | JSONB | NOT NULL |
| payload_hash | VARCHAR(128) | |
| source_url | TEXT | |
| processing_status | VARCHAR(30) | |
| processed_at | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | NOT NULL |

Recommended unique constraint:

```text
(provider_connection_id, provider_event_id)
```

## Immutability requirement

Once inserted:

```text
payload
event_type
provider_event_id
received_at
```

must not be modified.

Processing metadata such as:

```text
processing_status
processed_at
```

may be updated.

---

# 19. Canonical Event Layer

## 19.1 canonical_events

Provider-independent engineering events.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| raw_event_id | UUID | FK |
| organization_id | UUID | FK |
| team_id | UUID | FK |
| project_id | UUID | FK |
| repository_id | UUID | FK |
| event_type | VARCHAR(100) | |
| occurred_at | TIMESTAMPTZ | |
| actor_ref | VARCHAR(255) | |
| entity_type | VARCHAR(100) | |
| entity_id | VARCHAR(255) | |
| metadata | JSONB | |
| created_at | TIMESTAMPTZ | |

Examples of canonical event types:

```text
COMMIT
PULL_REQUEST
CODE_REVIEW
ISSUE_CREATED
ISSUE_UPDATED
DEPLOYMENT
BUILD
INCIDENT
```

---

# 20. Privacy-Aware Actor References

The canonical layer may need to associate events with application identities.

However, AI processing must use a sanitized representation.

Example:

```text
Database:

actor_reference = internal-user-123


AI request:

actor_reference = anonymous-actor-A
```

The mapping must never be sent to the cloud LLM.

---

# 21. commits

Optional specialized table for commit-specific information.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| canonical_event_id | UUID | FK |
| repository_id | UUID | FK |
| commit_hash | VARCHAR(255) | |
| branch | VARCHAR(255) | |
| additions | INTEGER | |
| deletions | INTEGER | |
| files_changed | INTEGER | |
| committed_at | TIMESTAMPTZ | |
| metadata | JSONB | |

---

# 22. pull_requests

Stores normalized pull/merge request information.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| canonical_event_id | UUID | FK |
| repository_id | UUID | FK |
| external_id | VARCHAR(255) | |
| title | TEXT | |
| source_branch | VARCHAR(255) | |
| target_branch | VARCHAR(255) | |
| status | VARCHAR(50) | |
| opened_at | TIMESTAMPTZ | |
| merged_at | TIMESTAMPTZ | |
| closed_at | TIMESTAMPTZ | |
| additions | INTEGER | |
| deletions | INTEGER | |
| files_changed | INTEGER | |

---

# 23. reviews

Stores code review events.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| pull_request_id | UUID | FK |
| reviewer_reference | VARCHAR(255) | |
| review_status | VARCHAR(50) | |
| submitted_at | TIMESTAMPTZ | |
| metadata | JSONB | |

This table stores operational engineering information, not a productivity score.

---

# 24. issues

Stores normalized issue/tracking data.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| canonical_event_id | UUID | FK |
| project_id | UUID | FK |
| external_id | VARCHAR(255) | |
| issue_type | VARCHAR(100) | |
| status | VARCHAR(100) | |
| priority | VARCHAR(50) | |
| created_at | TIMESTAMPTZ | |
| resolved_at | TIMESTAMPTZ | |

---

# 25. deployments

Stores normalized deployment events.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| canonical_event_id | UUID | FK |
| project_id | UUID | FK |
| environment | VARCHAR(100) | |
| status | VARCHAR(50) | |
| started_at | TIMESTAMPTZ | |
| completed_at | TIMESTAMPTZ | |
| version | VARCHAR(255) | |
| metadata | JSONB | |

---

# 26. Analytics Tables

## 26.1 metric_definitions

Defines available engineering metrics.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| name | VARCHAR(150) | UNIQUE |
| description | TEXT | |
| category | VARCHAR(100) | |
| calculation_definition | JSONB | |
| aggregation_level | VARCHAR(50) | |
| enabled | BOOLEAN | |
| created_at | TIMESTAMPTZ | |

Possible categories:

```text
DELIVERY
QUALITY
RELIABILITY
FLOW
CODE_REVIEW
DEPLOYMENT
```

---

# 27. metric_values

Stores calculated metrics.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| metric_definition_id | UUID | FK |
| organization_id | UUID | FK |
| project_id | UUID | FK |
| team_id | UUID | FK, nullable |
| repository_id | UUID | FK, nullable |
| aggregation_period | VARCHAR(30) | |
| period_start | TIMESTAMPTZ | |
| period_end | TIMESTAMPTZ | |
| value_numeric | DOUBLE PRECISION | |
| dimensions | JSONB | |
| calculated_at | TIMESTAMPTZ | |

### Important

Do not add:

```text
individual_productivity_score
developer_productivity
employee_productivity
```

or equivalent fields.

---

# 28. analytics_snapshots

Stores precomputed analytical summaries.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| organization_id | UUID | FK |
| project_id | UUID | FK |
| team_id | UUID | FK |
| snapshot_date | DATE | |
| metrics | JSONB | |
| generated_at | TIMESTAMPTZ | |

Useful for fast dashboard rendering.

---

# 29. Engineering Health Scores

## 29.1 engineering_health_scores

Stores engineering health results.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| organization_id | UUID | FK |
| project_id | UUID | FK |
| team_id | UUID | FK |
| period_start | TIMESTAMPTZ | |
| period_end | TIMESTAMPTZ | |
| score | DOUBLE PRECISION | |
| score_version | VARCHAR(50) | |
| component_metrics | JSONB | |
| calculated_at | TIMESTAMPTZ | |

The score should be associated primarily with:

```text
Organization
Project
Team
```

rather than individual developers.

---

# 30. engineering_trends

Stores detected trends.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| organization_id | UUID | FK |
| project_id | UUID | FK |
| team_id | UUID | FK |
| metric_id | UUID | FK |
| trend_type | VARCHAR(50) | |
| magnitude | DOUBLE PRECISION | |
| confidence | DOUBLE PRECISION | |
| detected_at | TIMESTAMPTZ | |
| metadata | JSONB | |

Examples:

```text
IMPROVING
DECLINING
STABLE
ANOMALY
```

---

# 31. ML Architecture Tables

## 31.1 analytics.ml_features

Stores extracted features for ML models.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| organization_id | UUID | FK |
| team_id | UUID | FK |
| target_entity_type | VARCHAR(50) | |
| target_entity_id | UUID | |
| feature_vector | JSONB | |
| generated_at | TIMESTAMPTZ | |

## 31.2 analytics.ml_predictions

Stores model inferences with required evidence and confidence.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| organization_id | UUID | FK |
| model_id | UUID | FK |
| prediction_type | VARCHAR(50) | |
| target_entity_id | UUID | |
| score | DOUBLE PRECISION | |
| confidence | DOUBLE PRECISION | NOT NULL |
| evidence | JSONB | NOT NULL |
| created_at | TIMESTAMPTZ | |

## 31.3 configuration.model_registry

Tracks global, org-adapted, and team-adapted models. No individual developer modeling.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| name | VARCHAR(150) | |
| version | VARCHAR(50) | |
| scope | VARCHAR(50) | GLOBAL, ORG, TEAM |
| organization_id | UUID | FK, nullable |
| team_id | UUID | FK, nullable |
| artifact_path | TEXT | |
| status | VARCHAR(30) | |
| created_at | TIMESTAMPTZ | |

## 31.4 analytics.training_jobs

Tracks model training tasks.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| model_registry_id | UUID | FK |
| status | VARCHAR(30) | |
| metrics | JSONB | |
| started_at | TIMESTAMPTZ | |
| completed_at | TIMESTAMPTZ | |

---

# 32. AI Tables

## 31.1 ai_insight_requests

Tracks requests sent through the AI Gateway.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| organization_id | UUID | FK |
| project_id | UUID | FK |
| requested_by | UUID | FK |
| model_provider | VARCHAR(100) | |
| model_name | VARCHAR(150) | |
| request_type | VARCHAR(100) | |
| sanitized_context | JSONB | |
| status | VARCHAR(30) | |
| created_at | TIMESTAMPTZ | |
| completed_at | TIMESTAMPTZ | |

The `sanitized_context` must not contain developer identity or secrets.

---

# 32. ai_insights

Stores AI-generated insights.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| request_id | UUID | FK |
| organization_id | UUID | FK |
| project_id | UUID | FK |
| insight_type | VARCHAR(100) | |
| title | TEXT | |
| content | TEXT | |
| confidence | DOUBLE PRECISION | |
| source_metrics | JSONB | |
| status | VARCHAR(30) | |
| created_at | TIMESTAMPTZ | |

AI output should be treated as an analytical recommendation, not authoritative raw data.

---

# 33. Audit Logs

## 33.1 audit_logs

Tracks security-sensitive and administrative actions.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| organization_id | UUID | FK |
| actor_user_id | UUID | FK |
| action | VARCHAR(150) | |
| resource_type | VARCHAR(100) | |
| resource_id | UUID | |
| previous_state | JSONB | |
| new_state | JSONB | |
| ip_address | INET | |
| user_agent | TEXT | |
| created_at | TIMESTAMPTZ | |

Audit logs should be append-only wherever possible.

---

# 34. Data Processing Jobs

## 34.1 data_processing_jobs

Tracks asynchronous processing.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| job_type | VARCHAR(100) | |
| raw_event_id | UUID | FK |
| status | VARCHAR(30) | |
| attempts | INTEGER | |
| started_at | TIMESTAMPTZ | |
| completed_at | TIMESTAMPTZ | |
| error_message | TEXT | |
| created_at | TIMESTAMPTZ | |

Example statuses:

```text
PENDING
PROCESSING
COMPLETED
FAILED
RETRYING
```

---

# 35. System Settings

## 35.1 system_settings

Stores configurable system behavior.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| organization_id | UUID | FK |
| setting_key | VARCHAR(150) | |
| setting_value | JSONB | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

Recommended unique constraint:

```text
(organization_id, setting_key)
```

Secrets should not be stored directly in this table.

---

# 36. Important Relationships

```text
organizations
      │
      ├── users
      │
      ├── teams
      │      └── team_members
      │
      ├── projects
      │      ├── repositories
      │      └── project_members
      │
      └── provider_connections
              │
              └── raw_provider_events
                         │
                         ▼
                  canonical_events
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       commits      pull_requests     issues
                         │
                      reviews
                         │
                         ▼
                    metrics
                         │
                         ▼
              engineering_health_scores
                         │
                         ▼
                    AI Gateway
                         │
                         ▼
                    ai_insights
```

---

# 37. Indexing Strategy

Important indexes should include:

## Raw events

```text
raw_provider_events(provider_connection_id)
raw_provider_events(provider_event_id)
raw_provider_events(received_at)
raw_provider_events(event_type)
raw_provider_events(processing_status)
```

## Canonical events

```text
canonical_events(organization_id)
canonical_events(project_id)
canonical_events(repository_id)
canonical_events(event_type)
canonical_events(occurred_at)
```

## Analytics

```text
metric_values(metric_definition_id)
metric_values(organization_id, period_start)
metric_values(project_id, period_start)
engineering_health_scores(project_id, period_start)
```

## Audit

```text
audit_logs(organization_id, created_at)
audit_logs(actor_user_id, created_at)
```

Indexes should be added based on actual query patterns and measured performance.

---

# 38. JSONB Usage

JSONB should be used for data that is genuinely variable.

Good candidates:

```text
Raw provider payload
Provider metadata
Canonical event metadata
Metric dimensions
AI sanitized context
AI source metrics
Configuration
```

Avoid putting core relational fields inside JSONB when they require frequent querying or constraints.

For example:

```text
GOOD:
repository_id UUID

LESS IDEAL:
metadata = {"repository_id": "..."}
```

---

# 39. Data Retention

Retention policies must distinguish between:

```text
Raw Events
Canonical Events
Analytics
Audit Logs
AI Insights
```

Raw provider events may require longer retention for:

- Reprocessing
- Auditing
- Debugging
- Historical analysis

Retention periods should be configurable according to deployment requirements.

---

# 40. Data Integrity

Database constraints should enforce:

- Foreign-key integrity
- Unique provider event identifiers
- Valid organization relationships
- Valid project relationships
- Required timestamps
- Valid metric references
- Valid provider references

Application-level validation should complement, not replace, database constraints.

---

# 41. Multi-Tenancy

All organization-owned data must be associated with:

```text
organization_id
```

Where appropriate.

Example:

```text
User
   ↓
Organization

Project
   ↓
Organization

Provider Connection
   ↓
Organization

Analytics
   ↓
Organization
```

Queries must enforce organization isolation.

---

# 42. Privacy Rules

The database design must enforce the following architectural separation:

```text
Operational Identity
        │
        ▼
Internal CodeSense Database
        │
        │
        X
        │
        ▼
Cloud LLM
```

The AI Gateway must construct a sanitized context from approved analytics rather than directly exposing database records.

---

# 43. Offline Operation

The database must support local operation without Internet access.

During offline operation:

```text
Local Provider Data
        ↓
Local PostgreSQL
        ↓
Canonical Processing
        ↓
Analytics
        ↓
Engineering Health
        ↓
Dashboard
```

Cloud AI may be unavailable.

The database itself must not depend on an external cloud database for core functionality.

---

# 44. Migration Strategy

Use version-controlled database migrations.

Recommended tool:

```text
Alembic
```

Migration workflow:

```text
Schema Change
      ↓
Create Migration
      ↓
Review Migration
      ↓
Run Tests
      ↓
Apply Migration
      ↓
Verify Schema
```

Never modify production schema manually without recording the equivalent migration.

---

# 45. Backup and Recovery

The deployment must support:

- PostgreSQL backups
- Backup verification
- Point-in-time recovery where required
- Restore testing
- Migration recovery
- Disaster recovery procedures

Backups must not expose credentials or sensitive data unnecessarily.

---

# 46. Database Environment Separation

Recommended environments:

```text
Development
     ↓
Testing
     ↓
Staging
     ↓
Production
```

Each environment should have an isolated database.

Production data must not be copied into development environments without appropriate sanitization.

---

# 47. Definition of Done

The database implementation is complete when:

- [ ] All required tables are implemented.
- [ ] Foreign keys are configured.
- [ ] Required unique constraints are implemented.
- [ ] Required indexes are implemented.
- [ ] Raw provider events are immutable except processing metadata.
- [ ] Canonical event model is implemented.
- [ ] Cross-provider analytics operate on canonical data.
- [ ] Individual productivity score fields do not exist.
- [ ] Engineering Health Score tables are implemented.
- [ ] AI request data is privacy-sanitized.
- [ ] Developer identity cannot enter cloud-AI context.
- [ ] Audit logging is implemented.
- [ ] Background job tracking is implemented.
- [ ] Multi-tenant isolation is enforced.
- [ ] Database migrations are version controlled.
- [ ] Backup and restore procedures are tested.
- [ ] Offline database operation works.
- [ ] Database integration tests pass.

---

# 48. Schema Evolution Rule

This schema is editable during implementation.

Any structural change must answer:

```text
1. Why is the change required?
2. Which requirement does it support?
3. Does it affect privacy?
4. Does it affect raw-event immutability?
5. Does it affect canonical analytics?
6. Does it introduce individual productivity scoring?
7. Does it affect offline functionality?
8. Does it require a migration?
9. Does it affect the API?
10. Does it require new acceptance tests?
```

If the change affects a locked architectural decision, it must be explicitly reviewed before implementation.

---

# 49. Locked Database Constraints

The following constraints are **non-negotiable**:

```text
RAW EVENTS
──────────
Raw provider payloads must remain preserved.

CANONICAL DATA
──────────────
Cross-provider analytics must use the canonical layer.

PRIVACY
───────
Developer identity must never be sent to a cloud LLM.

PRODUCTIVITY
────────────
Individual productivity scores must not be stored or calculated.

OFFLINE
───────
Core database-backed analytics must work without Internet access.

AI
──
AI is an optional analytical layer and must not become
the source of truth for CodeSense engineering data.
```

---

# 50. Final Database Architecture

```text
                    ┌──────────────────────┐
                    │    Organizations     │
                    └──────────┬───────────┘
                               │
             ┌─────────────────┼──────────────────┐
             │                 │                  │
             ▼                 ▼                  ▼
          Users              Teams             Projects
             │                 │                  │
             │                 │            ┌─────┴─────┐
             │                 │            ▼           ▼
             │                 │       Repositories  Members
             │                 │            │
             │                 │            ▼
             │                 │    Provider Connections
             │                 │            │
             │                 │            ▼
             │                 │    Raw Provider Events
             │                 │            │
             │                 │            ▼
             │                 │    Canonical Events
             │                 │            │
             │                 │     ┌──────┼──────┐
             │                 │     ▼      ▼      ▼
             │                 │  Commits  PRs   Issues
             │                 │            │
             │                 │         Reviews
             │                 │            │
             │                 └────────────┤
             │                              ▼
             │                         Metrics
             │                              │
             │                              ▼
             │                    Engineering Health
             │                              │
             │                              ▼
             │                         AI Gateway
             │                              │
             │                         Sanitization
             │                              │
             │                              ▼
             │                          AI Insights
             │
             └──────────────────────────────┐
                                            ▼
                                       Audit Logs
```

**Source of truth:** PostgreSQL  
**Raw data:** Immutable provider events  
**Analytical foundation:** Canonical event layer  
**Engineering intelligence:** Analytics + Engineering Health  
**AI:** Optional, privacy-controlled insight layer  
**Individual productivity scoring:** Not supported