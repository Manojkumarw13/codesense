# CodeSense — Implementation Plan

**Version:** 1.0  
**Project:** CodeSense Engineering Analytics Platform  
**Implementation Strategy:** Sequential, phase-based development  
**Primary Goal:** Build CodeSense from foundation to a complete demonstrable engineering analytics platform.

---

# 1. Implementation Strategy

CodeSense will be implemented **chronologically**.

Each phase depends on the previous phase being functional.

```text
Phase 0: Project Definition & Finalization
      ↓
Phase 1: Development Environment
      ↓
Phase 2: Database Foundation
      ↓
Phase 3: Backend Foundation
      ↓
Phase 4: Real-Time Simulator
      ↓
Phase 5: Event Ingestion Pipeline
      ↓
Phase 6: Canonical Data Layer
      ↓
Phase 7: Analytics Engine
      ↓
Phase 8: Engineering Health Score
      ↓
Phase 9: Bottleneck & Anomaly Detection
      ↓
Phase 10: Insights Engine
      ↓
Phase 11: Frontend Foundation
      ↓
Phase 12: Dashboard Implementation
      ↓
Phase 13: AI Intelligence Layer
      ↓
Phase 14: Privacy & Offline Mode
      ↓
Phase 15: Real Provider Integrations
      ↓
Phase 16: Authentication & RBAC
      ↓
Phase 17: Testing & Validation
      ↓
Phase 18: Deployment
      ↓
Phase 19: Observability
      ↓
Phase 20: Security Hardening
      ↓
Phase 21: Documentation
      ↓
Phase 22: Final End-to-End Validation
      ↓
Phase 23: Final Demonstration Preparation
```

---

# Phase 0 — Project Definition & Finalization

## Objective

Freeze the technical and product requirements before writing production code.

### Tasks

- [ ] Review the CodeSense PRD.
- [ ] Review the CodeSense TRD.
- [ ] Review the Backend Schema.
- [ ] Review the Application Flow.
- [ ] Confirm the MVP scope.
- [ ] Confirm the initial engineering metrics.
- [ ] Confirm the Engineering Health Score dimensions.
- [ ] Confirm privacy requirements.
- [ ] Confirm offline requirements.
- [ ] Confirm simulator requirements.
- [ ] Confirm the initial provider strategy.
- [ ] Define what is explicitly outside the MVP.
- [ ] Create the initial Git repository.

### Deliverables

```text
PRD
TRD
Backend Schema
Application Flow
Implementation Plan
MVP Scope
Git Repository
```

### Completion Criteria

The project requirements are stable enough to begin implementation.

---

# Phase 1 — Development Environment

## Objective

Create a reproducible development environment.

### Tasks

### 1.1 Repository Structure

Create:

```text
codesense/
├── backend/
├── frontend/
├── simulator/
├── database/
├── tests/
├── docs/
├── scripts/
└── docker/
```

### 1.2 Backend Environment

- [ ] Install Python.
- [ ] Create virtual environment.
- [ ] Install FastAPI.
- [ ] Install Uvicorn.
- [ ] Install Pydantic.
- [ ] Install SQLAlchemy.
- [ ] Install Alembic.
- [ ] Install PostgreSQL driver.
- [ ] Install pytest.

### 1.3 Development Tools

- [ ] Git
- [ ] GitHub/GitLab repository
- [ ] VS Code
- [ ] Docker
- [ ] Docker Compose

### 1.4 Configuration

Create:

```text
.env.example
.gitignore
README.md
```

### Completion Criteria

The backend starts successfully with a basic health endpoint.

---

# Phase 2 — Database Foundation ✅

## Objective

Implement the PostgreSQL database architecture.

### Tasks

### 2.1 PostgreSQL

- [x] Start PostgreSQL.
- [x] Create CodeSense database.
- [x] Configure database connection.
- [x] Test connection from Python.

### 2.2 Database Schemas

Create:

```text
raw
core
analytics
configuration
audit
```

### 2.3 Core Tables

Create in order:

```text
organizations
teams
repositories
projects
work_items
changes
reviews
builds
deployments
incidents
canonical_events
```

### 2.4 Raw Table

Create:

```text
raw.provider_events
```

### 2.5 Analytics Tables

Create:

```text
metric_definitions
metric_values
health_scores
health_score_components
anomalies
bottlenecks
insights
```

### 2.6 Database Migrations

- [x] Configure Alembic.
- [x] Create initial migration.
- [x] Test migration.
- [x] Test rollback.

### 2.7 Indexes

Implement required indexes.

### Completion Criteria

The complete MVP database schema can be created from a clean database using migrations.

---

# Phase 3 — Backend Foundation ✅

## Objective

Create the basic FastAPI backend architecture.

### Tasks

### 3.1 Application Structure

Implement:

```text
backend/app/
├── main.py
├── core/
├── api/
├── models/
├── schemas/
├── services/
├── repositories/
└── utils/
```

### 3.2 Configuration

Implement:

- [x] Environment configuration.
- [x] Database configuration.
- [x] Logging configuration.
- [x] Application settings.

### 3.3 API

Create:

```text
GET /api/v1/health
```

### 3.4 Database Layer

- [x] SQLAlchemy models.
- [x] Database session.
- [x] Repository pattern where useful.
- [x] Transaction handling.

### 3.5 Error Handling

Implement standardized:

```text
400
401
403
404
409
422
500
```

responses.

### Completion Criteria

FastAPI can communicate with PostgreSQL and return reliable API responses.

---

# Phase 4 — Real-Time Engineering Data Simulator ✅

## Objective

Build the data-generation system before integrating real providers.

The simulator is a **data source**, not the CodeSense analytics system.

---

## 4.1 Simulator Architecture

```text
Scenario
   ↓
Entity Generator
   ↓
Event Generator
   ↓
Event Stream
   ↓
CodeSense Ingestion API
```

---

## 4.2 Entity Generator

Implement generators for:

- [x] Organizations
- [x] Teams
- [x] Repositories
- [x] Projects
- [x] Work items
- [x] Changes
- [x] Reviews
- [x] Builds
- [x] Deployments
- [x] Incidents

---

## 4.3 Event Generator

Implement:

```text
WORK_ITEM_CREATED
WORK_ITEM_STARTED
WORK_ITEM_COMPLETED

CHANGE_CREATED
CHANGE_MERGED
CHANGE_CLOSED

REVIEW_REQUESTED
REVIEW_COMPLETED

BUILD_STARTED
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

## 4.4 Simulator Scenarios

Implement sequentially:

### Scenario 1

- [x] Normal engineering activity.

### Scenario 2

- [x] High workload.

### Scenario 3

- [x] Review bottleneck.

### Scenario 4

- [x] CI bottleneck.

### Scenario 5

- [x] Deployment failures.

### Scenario 6

- [x] Incident spike.

### Scenario 7

- [x] Recovery.

---

## 4.5 Simulator Controls

Implement:

```text
START
STOP
PAUSE
RESUME
STATUS
SCENARIO
```

### Completion Criteria

The simulator can generate realistic correlated engineering events continuously.

---

# Phase 5 — Event Ingestion Pipeline ✅

## Objective

Make CodeSense capable of receiving engineering events.

---

## 5.1 Event API

Implement:

```text
POST /api/v1/events
POST /api/v1/events/batch
GET  /api/v1/events
```

---

## 5.2 Event Validation

Implement validation for:

- [x] Provider.
- [x] Event ID.
- [x] Event type.
- [x] Timestamp.
- [x] Payload.
- [x] Source.

---

## 5.3 Deduplication

Implement:

```text
provider + external_event_id
```

as the primary idempotency mechanism.

---

## 5.4 Raw Storage

Implement:

```text
Incoming Event
      ↓
Validation
      ↓
Deduplication
      ↓
raw.provider_events
```

---

## 5.5 Processing Status

Implement:

```text
PENDING
PROCESSING
PROCESSED
FAILED
```

---

## 5.6 Error Handling

Implement an event quarantine/dead-letter mechanism for invalid or unprocessable events.

### Completion Criteria

The simulator can send thousands of events through the ingestion API and all valid events are stored reliably.

---

# Phase 6 — Canonical Data Layer ✅

## Objective

Convert provider-specific events into CodeSense's provider-independent model.

---

## 6.1 Normalization Framework

Create:

```text
normalization/
├── base.py
├── github.py
├── gitlab.py
├── jira.py
└── simulator.py
```

---

## 6.2 Canonical Event Mapping

Implement mappings such as:

```text
GitHub PR Opened
        ↓
CHANGE_CREATED

GitLab MR Created
        ↓
CHANGE_CREATED
```

and:

```text
GitHub PR Review
        ↓
REVIEW_COMPLETED
```

---

## 6.3 Canonical Entity Creation

Convert events into:

```text
teams
repositories
projects
work_items
changes
reviews
builds
deployments
incidents
```

---

## 6.4 Relationship Resolution

Connect:

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

where source data supports the relationship.

---

## 6.5 Actor Handling

Implement internal `actor_ref` support where necessary.

Do **not** create individual productivity analytics.

### Completion Criteria

Different provider-shaped events can be converted into the same canonical model.

---

# Phase 7 — Analytics Engine

## Objective

Calculate engineering metrics from canonical data.

---

## 7.1 Metric Framework

Create a generic metric engine:

```text
Metric Definition
       ↓
Data Query
       ↓
Calculation
       ↓
Aggregation
       ↓
metric_values
```

---

## 7.2 Implement Metrics in This Order

### Delivery

1. [ ] Deployment Frequency
2. [ ] Lead Time for Changes
3. [ ] Cycle Time
4. [ ] Throughput
5. [ ] Work-in-Progress

### Development

6. [ ] PR/MR Cycle Time
7. [ ] Review Turnaround
8. [ ] Review Backlog
9. [ ] Change Size

### CI/CD

10. [ ] Build Success Rate
11. [ ] Build Failure Rate
12. [ ] Pipeline Duration
13. [ ] Deployment Success Rate
14. [ ] Deployment Failure Rate
15. [ ] Rollback Rate

### Reliability

16. [ ] Change Failure Rate
17. [ ] Incident Frequency
18. [ ] MTTR

---

## 7.3 Time Aggregations

Implement:

```text
Hourly
Daily
Weekly
Monthly
Custom Range
```

---

## 7.4 Baselines

Implement:

```text
Current Period
       ↓
Historical Baseline
       ↓
Percentage Change
```

### Completion Criteria

All MVP metrics are calculated correctly from canonical events.

---

# Phase 8 — Engineering Health Score

## Objective

Create the central CodeSense Engineering Health Score.

---

## 8.1 Dimensions

Implement:

```text
Delivery Flow
Development Flow
Review Flow
CI/CD Reliability
Deployment Health
Operational Health
```

---

## 8.2 Normalization

Convert different metrics into comparable scores.

```text
Raw Metric
    ↓
Normalization
    ↓
0–100 Dimension Score
```

---

## 8.3 Weighting

Initial weights:

```text
Delivery Flow       20%
Development Flow    20%
Review Flow         15%
CI/CD Reliability   15%
Deployment Health   15%
Operational Health  15%
```

Keep weights configurable.

---

## 8.4 Score Calculation

Implement:

```text
Dimension Scores
       ↓
Weighted Contributions
       ↓
Engineering Health Score
```

---

## 8.5 Explainability

Implement:

```text
Score
 ↓
Dimension
 ↓
Metrics
 ↓
Evidence
```

---

## 8.6 Historical Score

Store:

```text
Current Score
Previous Score
Score Change
```

### Completion Criteria

CodeSense produces a reproducible and explainable team-level Engineering Health Score.

---

# Phase 9 — Bottleneck & Anomaly Detection

## Objective

Identify engineering workflow problems automatically.

---

## 9.1 Bottleneck Detection

Implement in this order:

### Review Bottleneck

```text
Review Backlog ↑
+
Review Turnaround ↑
```

### CI Bottleneck

```text
Pipeline Duration ↑
OR
Failure Rate ↑
```

### Deployment Bottleneck

```text
Deployment Failure ↑
OR
Rollback Rate ↑
```

### Workflow Bottleneck

```text
WIP ↑
+
Cycle Time ↑
```

---

## 9.2 Anomaly Detection

Start with:

- [ ] Rolling averages.
- [ ] Percentage change.
- [ ] Z-score.
- [ ] Baseline comparison.

---

## 9.3 Severity

Implement:

```text
LOW
MEDIUM
HIGH
CRITICAL
```

---

## 9.4 Evidence

Every anomaly/bottleneck must store the metrics that caused detection.

### Completion Criteria

The simulator's bottleneck scenarios automatically produce the expected CodeSense detections.

---

# Phase 10 — Insights Engine

## Objective

Convert metrics, anomalies, and bottlenecks into structured engineering insights.

---

## 10.1 Rule-Based Insights

Implement first.

Example:

```text
IF
review_backlog ↑
AND
review_turnaround ↑

THEN

Review Flow is becoming a bottleneck.
```

---

## 10.2 Insight Structure

Every insight should contain:

```text
Title
Description
Severity
Category
Evidence
Affected Team
Generated By
Timestamp
```

---

## 10.3 Insight Lifecycle

```text
Detected
   ↓
Active
   ↓
Reviewed
   ↓
Resolved
   ↓
Archived
```

### Completion Criteria

CodeSense can automatically explain significant engineering changes using deterministic analytical rules.

---

# Phase 11 — Frontend Foundation

## Objective

Create the CodeSense user interface.

---

## 11.1 Frontend Setup

If using React:

- [ ] Create React application.
- [ ] Configure TypeScript.
- [ ] Configure routing.
- [ ] Configure API client.
- [ ] Create shared UI components.

---

## 11.2 Application Layout

Implement:

```text
Sidebar
Header
Team Selector
Time Range Selector
Main Content
Notifications
User Menu
```

---

## 11.3 Navigation

Implement:

```text
Overview
Engineering Health
Delivery
Development Flow
CI/CD
Reliability
Insights
Anomalies
Bottlenecks
Trends
Integrations
Simulator
AI Analysis
Settings
```

### Completion Criteria

The frontend can navigate between all major application sections.

---

# Phase 12 — Dashboard Implementation

## Objective

Connect the frontend to real CodeSense analytics.

---

## 12.1 Overview Dashboard

Implement:

- [ ] Engineering Health Score.
- [ ] Score change.
- [ ] Dimension scores.
- [ ] Delivery summary.
- [ ] Development summary.
- [ ] CI/CD summary.
- [ ] Reliability summary.
- [ ] Active bottlenecks.
- [ ] Active anomalies.
- [ ] Latest insights.

---

## 12.2 Health Dashboard

Implement:

```text
Score
 ↓
Components
 ↓
Historical Trend
 ↓
Contributing Metrics
 ↓
Evidence
```

---

## 12.3 Delivery Dashboard

Implement:

- [ ] Deployment Frequency.
- [ ] Lead Time.
- [ ] Cycle Time.
- [ ] Throughput.
- [ ] WIP.

---

## 12.4 Development Dashboard

Implement:

- [ ] PR/MR volume.
- [ ] Review turnaround.
- [ ] Review backlog.
- [ ] Change cycle time.
- [ ] Change size.

---

## 12.5 CI/CD Dashboard

Implement:

- [ ] Build success.
- [ ] Build failure.
- [ ] Pipeline duration.
- [ ] Deployment success.
- [ ] Deployment failure.
- [ ] Rollback rate.

---

## 12.6 Reliability Dashboard

Implement:

- [ ] Incident frequency.
- [ ] MTTR.
- [ ] Change failure rate.
- [ ] Deployment failures.
- [ ] Rollbacks.

---

## 12.7 Insights Dashboard

Implement:

- [ ] Insights list.
- [ ] Insight details.
- [ ] Evidence.
- [ ] Related metrics.
- [ ] Related anomalies.
- [ ] Related bottlenecks.

### Completion Criteria

A user can operate CodeSense entirely through the dashboard using simulator-generated data.

---

# Phase 13 — AI Intelligence Layer

## Objective

Add optional AI-powered engineering explanations.

**Do this only after deterministic analytics are working.**

---

## 13.1 AI Architecture

```text
Analytics
   ↓
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

## 13.2 Privacy Gateway

Implement:

- [ ] Developer name removal.
- [ ] Email removal.
- [ ] Username removal.
- [ ] Developer ID removal.
- [ ] Raw payload exclusion.
- [ ] Individual metric exclusion.
- [ ] Payload validation.

---

## 13.3 AI Use Cases

Implement in this order:

### 1. Score Explanation

> Why did the Engineering Health Score change?

### 2. Anomaly Explanation

> What changed and why is it unusual?

### 3. Bottleneck Explanation

> Why is this workflow becoming a bottleneck?

### 4. Trend Summary

> Summarize this team's engineering trend.

### 5. Investigation Suggestions

> What should the engineering team investigate?

---

## 13.4 AI Provider

Use the selected cloud/local LLM integration.

For the prototype, the AI layer can use an OpenRouter-compatible model.

### Completion Criteria

AI can explain team-level analytics without receiving developer identity.

---

# Phase 14 — Privacy & Offline Mode

## Objective

Make the project's locked privacy and offline requirements operational.

---

## 14.1 Privacy Audit

Check:

- [ ] No individual productivity score exists.
- [ ] No developer ranking exists.
- [ ] No unnecessary personal information is exposed.
- [ ] Cloud AI payloads contain no developer identity.
- [ ] Raw event access is restricted.

---

## 14.2 Small-Team Privacy

Implement appropriate controls such as:

- [ ] Minimum aggregation thresholds.
- [ ] Restricted drill-down.
- [ ] Role-based access.
- [ ] Identity masking where appropriate.

---

## 14.3 Offline Detection

Implement:

```text
Internet Available
        ↓
Normal Mode

Internet Unavailable
        ↓
Offline Mode
```

---

## 14.4 Offline Core

Verify:

```text
Raw Storage          ✓
Canonicalization     ✓
Metrics              ✓
Health Score         ✓
Historical Analytics ✓
Dashboard            ✓
```

---

## 14.5 AI Offline Behavior

When Internet is unavailable:

```text
Cloud AI
   ↓
Unavailable
```

But:

```text
Core Analytics
   ↓
Continues Normally
```

### Completion Criteria

The system can operate its core analytics without Internet connectivity.

---

# Phase 15 — Real Provider Integrations

## Objective

Replace the simulator-only environment with real engineering data sources.

**Do this only after the simulator has validated the entire pipeline.**

---

## 15.1 First Provider

Implement one version-control provider first.

Recommended sequence:

```text
GitHub
   ↓
GitLab
   ↓
Jira
   ↓
CI/CD Provider
```

---

## 15.2 Provider Connector

For each provider implement:

- [ ] Authentication.
- [ ] API client.
- [ ] Pagination.
- [ ] Rate-limit handling.
- [ ] Event retrieval.
- [ ] Webhooks where appropriate.
- [ ] Provider → canonical mapping.
- [ ] Error handling.
- [ ] Sync state.

---

## 15.3 Provider Validation

Verify:

```text
Provider
   ↓
Connector
   ↓
Raw Event
   ↓
Canonical Event
   ↓
Analytics
```

---

## 15.4 Cross-Provider Test

Send equivalent events from two providers.

Expected:

```text
Provider A Event
       ↓
Canonical Event

Provider B Event
       ↓
Same Canonical Event Type
```

### Completion Criteria

CodeSense can perform analytics independently of the original provider.

---

# Phase 16 — Authentication & RBAC

## Objective

Secure the application for realistic multi-user usage.

---

## Tasks

- [ ] Implement authentication.
- [ ] Implement session/token management.
- [ ] Implement organization access.
- [ ] Implement team-level permissions.
- [ ] Implement roles.
- [ ] Implement protected APIs.
- [ ] Implement protected dashboard routes.

### Roles

```text
ADMIN
ENGINEERING_LEADER
ENGINEERING_MANAGER
TECH_LEAD
ANALYST
DEVELOPER
```

### Completion Criteria

Users can only access data allowed by their role and team permissions.

---

# Phase 17 — Testing & Validation

## Objective

Validate the complete system before deployment.

---

## 17.1 Unit Tests

Test:

- [ ] Event validation.
- [ ] Deduplication.
- [ ] Normalization.
- [ ] Metric calculations.
- [ ] Health Score calculations.
- [ ] Anomaly detection.
- [ ] Bottleneck detection.
- [ ] Privacy filtering.

---

## 17.2 Integration Tests

Test:

```text
Simulator
   ↓
Ingestion
   ↓
Raw Database
   ↓
Canonical Layer
   ↓
Analytics
   ↓
Dashboard
```

---

## 17.3 Privacy Tests

Attempt to send:

```text
Developer Name
Developer Email
Developer ID
Individual Metrics
```

to the AI gateway.

Expected:

```text
REQUEST BLOCKED
```

---

## 17.4 Offline Tests

Disable Internet.

Verify:

```text
Metrics          ✓
Health Score     ✓
Dashboard        ✓
Historical Data  ✓
Cloud AI         ✗
```

---

## 17.5 Scenario Tests

Run:

```text
NORMAL
REVIEW_BOTTLENECK
CI_BOTTLENECK
DEPLOYMENT_FAILURE
INCIDENT_SPIKE
RECOVERY
```

Verify that CodeSense responds correctly.

---

## 17.6 Performance Tests

Test:

- [ ] Event ingestion rate.
- [ ] API latency.
- [ ] Database query performance.
- [ ] Dashboard loading.
- [ ] Simulator throughput.
- [ ] Analytics processing latency.

### Completion Criteria

All critical test cases pass.

---

# Phase 18 — Deployment

## Objective

Create a reproducible deployment environment.

---

## 18.1 Docker Services

Initial deployment:

```text
codesense-api
codesense-worker (optional)
codesense-simulator
postgres
redis (optional/deferred for MVP)
codesense-dashboard
nginx
```

---

## 18.2 Docker Compose

Create:

```text
docker-compose.yml
```

Implement:

- [ ] Service networking.
- [ ] Persistent volumes.
- [ ] Environment configuration.
- [ ] Health checks.
- [ ] Restart policies.

---

## 18.3 Database Persistence

Verify:

```text
Container Restart
       ↓
Database Data Preserved
```

---

## 18.4 Logging

Implement:

- [ ] Application logs.
- [ ] Ingestion logs.
- [ ] Connector logs.
- [ ] Analytics logs.
- [ ] AI logs.
- [ ] Error logs.

---

## 18.5 Backup

Implement database backup and restore testing.

### Completion Criteria

CodeSense can be deployed from scratch and restarted without losing persistent data.

---

# Phase 19 — Observability

## Objective

Make the system operationally observable.

---

## Tasks

Monitor:

```text
API
│
├── Request Count
├── Latency
└── Error Rate

Ingestion
│
├── Events Received
├── Events Processed
├── Events Failed
└── Duplicate Events

Database
│
├── Connections
├── Query Performance
└── Storage

Analytics
│
├── Processing Time
├── Metric Calculations
└── Detection Rate

Connectors
│
├── Provider Status
├── Sync Status
└── API Errors
```

### Completion Criteria

Major system failures can be identified from logs/metrics without manually inspecting the application.

---

# Phase 20 — Security Hardening

## Objective

Prepare the system for a realistic deployment.

### Tasks

- [ ] Remove all hard-coded secrets.
- [ ] Rotate development credentials.
- [ ] Validate authentication.
- [ ] Validate authorization.
- [ ] Secure API endpoints.
- [ ] Secure webhook endpoints.
- [ ] Add rate limiting.
- [ ] Validate user input.
- [ ] Review SQL injection risks.
- [ ] Review XSS risks.
- [ ] Review CSRF requirements.
- [ ] Review Docker permissions.
- [ ] Review database permissions.
- [ ] Review logs for secret leakage.
- [ ] Review AI payloads for identity leakage.

### Completion Criteria

No critical security issue remains in the MVP.

---

# Phase 21 — Documentation

## Objective

Document the complete system.

Create:

```text
docs/
├── architecture.md
├── backend-schema.md
├── api.md
├── simulator.md
├── metrics.md
├── health-score.md
├── privacy.md
├── offline-mode.md
├── integrations.md
├── deployment.md
├── testing.md
└── troubleshooting.md
```

Also update:

```text
README.md
```

with:

- [ ] Project overview.
- [ ] Architecture.
- [ ] Installation.
- [ ] Environment configuration.
- [ ] Database setup.
- [ ] Simulator setup.
- [ ] Backend startup.
- [ ] Frontend startup.
- [ ] Docker deployment.
- [ ] API usage.
- [ ] Demonstration instructions.

---

# Phase 22 — Final End-to-End Validation

## Objective

Validate CodeSense as a complete product.

Run the following sequence.

### Test 1 — Normal Engineering

```text
Start Simulator
       ↓
Normal Scenario
       ↓
Events Generated
       ↓
Analytics Updated
       ↓
Health Score Stable
```

---

### Test 2 — Review Bottleneck

```text
Switch Scenario
       ↓
REVIEW_BOTTLENECK
       ↓
Review Delay ↑
       ↓
Review Backlog ↑
       ↓
Review Turnaround ↑
       ↓
Health Score ↓
       ↓
Bottleneck Detected
       ↓
Insight Generated
```

---

### Test 3 — CI Bottleneck

```text
CI Bottleneck
       ↓
Build Failures ↑
       ↓
Pipeline Duration ↑
       ↓
CI Reliability ↓
       ↓
Health Score ↓
       ↓
CI Bottleneck Detected
```

---

### Test 4 — Deployment Incident

```text
Deployment Failure
       ↓
Rollback
       ↓
Incident
       ↓
MTTR
       ↓
Operational Health ↓
       ↓
Health Score ↓
```

---

### Test 5 — Recovery

```text
Recovery Scenario
       ↓
Metrics Return Toward Baseline
       ↓
Bottleneck Resolves
       ↓
Reliability Improves
       ↓
Health Score Recovers
```

---

### Test 6 — AI Explanation

```text
Health Score ↓
       ↓
User asks:
"Why?"
       ↓
Team Metrics
       ↓
Privacy Gateway
       ↓
Sanitized Payload
       ↓
AI
       ↓
Explanation
```

---

### Test 7 — Offline

```text
Disable Internet
       ↓
Core Analytics
       ↓
Still Works
       ↓
AI
       ↓
Unavailable
```

### Completion Criteria

All seven scenarios work correctly.

---

# Phase 23 — Final Demonstration Preparation

## Objective

Prepare the project for academic/project evaluation.

---

## Demonstration Sequence

### Step 1

Open CodeSense.

### Step 2

Show the architecture.

```text
Data Sources
     ↓
Ingestion
     ↓
Raw Data
     ↓
Canonical Layer
     ↓
Analytics
```

### Step 3

Start simulator.

### Step 4

Show normal engineering activity.

### Step 5

Display Engineering Health Score.

### Step 6

Switch to Review Bottleneck scenario.

### Step 7

Show metrics changing in real time.

### Step 8

Show Health Score decreasing.

### Step 9

Open Bottlenecks.

### Step 10

Open the detected Review Bottleneck.

### Step 11

Show evidence.

### Step 12

Ask AI for an explanation.

### Step 13

Show the privacy-safe AI payload.

### Step 14

Disable Internet.

### Step 15

Show that core analytics continue working.

### Step 16

Show Cloud AI as unavailable.

### Step 17

Switch to Recovery.

### Step 18

Show the Health Score recovering.

---

# 24. Recommended Chronological Build Order

The actual coding order should be:

```text id="w9lywi"
01. Finalize Requirements
        ↓
02. Create Git Repository
        ↓
03. Setup Python / FastAPI
        ↓
04. Setup PostgreSQL
        ↓
05. Create Database Schemas
        ↓
06. Configure Alembic
        ↓
07. Create Database Models
        ↓
08. Create FastAPI Foundation
        ↓
09. Build Simulator Entities
        ↓
10. Build Simulator Events
        ↓
11. Build Simulator Scenarios
        ↓
12. Build Event Ingestion API
        ↓
13. Implement Validation
        ↓
14. Implement Deduplication
        ↓
15. Store Raw Events
        ↓
16. Build Normalization Framework
        ↓
17. Build Canonical Event Layer
        ↓
18. Build Canonical Entity Processing
        ↓
19. Implement Delivery Metrics
        ↓
20. Implement Development Metrics
        ↓
21. Implement CI/CD Metrics
        ↓
22. Implement Reliability Metrics
        ↓
23. Implement Historical Aggregation
        ↓
24. Implement Engineering Health Score
        ↓
25. Implement Score Explainability
        ↓
26. Implement Bottleneck Detection
        ↓
27. Implement Anomaly Detection
        ↓
28. Implement Insights Engine
        ↓
29. Build Frontend Foundation
        ↓
30. Build Overview Dashboard
        ↓
31. Build Analytics Dashboards
        ↓
32. Build Insights / Anomalies UI
        ↓
33. Build Simulator UI
        ↓
34. Implement Authentication
        ↓
35. Implement RBAC
        ↓
36. Build Privacy Gateway
        ↓
37. Integrate AI
        ↓
38. Implement Offline Mode
        ↓
39. Integrate First Real Provider
        ↓
40. Integrate Additional Providers
        ↓
41. Unit Testing
        ↓
42. Integration Testing
        ↓
43. Privacy Testing
        ↓
44. Offline Testing
        ↓
45. Performance Testing
        ↓
46. Security Hardening
        ↓
47. Docker Deployment
        ↓
48. Observability
        ↓
49. Documentation
        ↓
50. Final End-to-End Testing
        ↓
51. Final Demonstration
```

---

# 25. Phase Dependency Map

```text
Requirements
     │
     ▼
Environment
     │
     ▼
Database
     │
     ▼
Backend
     │
     ▼
Simulator
     │
     ▼
Ingestion
     │
     ▼
Canonical Layer
     │
     ▼
Analytics
     │
     ▼
Health Score
     │
     ▼
Detection
     │
     ▼
Insights
     │
     ├───────────────┐
     ▼               ▼
Frontend          AI Layer
     │               │
     └───────┬───────┘
             ▼
        Privacy/Offline
             │
             ▼
      Real Integrations
             │
             ▼
          Testing
             │
             ▼
        Deployment
             │
             ▼
       Demonstration
```

---

# 26. MVP Completion Checklist

## Foundation

- [ ] Repository created.
- [ ] Development environment configured.
- [ ] PostgreSQL running.
- [ ] Database migrations working.
- [ ] FastAPI running.

## Data

- [ ] Simulator working.
- [ ] Event ingestion working.
- [ ] Raw event storage working.
- [ ] Deduplication working.
- [ ] Canonicalization working.

## Analytics

- [ ] Delivery metrics working.
- [ ] Development metrics working.
- [ ] CI/CD metrics working.
- [ ] Reliability metrics working.
- [ ] Historical trends working.
- [ ] Engineering Health Score working.

## Intelligence

- [ ] Bottleneck detection working.
- [ ] Anomaly detection working.
- [ ] Insights working.

## Frontend

- [ ] Overview dashboard working.
- [ ] Health dashboard working.
- [ ] Delivery dashboard working.
- [ ] Development dashboard working.
- [ ] CI/CD dashboard working.
- [ ] Reliability dashboard working.
- [ ] Insights dashboard working.
- [ ] Simulator dashboard working.

## AI

- [ ] Privacy gateway working.
- [ ] Developer identity removed.
- [ ] AI explanation working.
- [ ] AI failure fallback working.

## Privacy

- [ ] No individual productivity scores.
- [ ] No individual ranking.
- [ ] Access controls implemented.
- [ ] Small-team privacy considered.

## Offline

- [ ] Core analytics work offline.
- [ ] Health Score works offline.
- [ ] Historical analytics work offline.
- [ ] Cloud AI correctly becomes unavailable.

## Production Readiness

- [ ] Authentication.
- [ ] RBAC.
- [ ] Security review.
- [ ] Logging.
- [ ] Monitoring.
- [ ] Docker deployment.
- [ ] Database backup.
- [ ] Documentation.

---

# 27. Final Definition of Done

CodeSense is considered **MVP-complete** when the following complete workflow works without manual intervention:

```text
┌─────────────────────┐
│ Real-Time Simulator │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│   Ingestion API     │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ Immutable Raw Data  │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ Canonical Data      │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ Analytics Engine    │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ Engineering Health  │
│ Score               │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ Anomaly Detection   │
│ Bottleneck Detection│
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ Insights Engine     │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ CodeSense Dashboard │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ Optional AI         │
│ Explanation         │
└─────────────────────┘
```

The implementation should **not jump directly to AI, dashboards, or real-provider integrations**. The chronological dependency is:

> **Data foundation → ingestion → canonical model → analytics → Health Score → detection → UI → AI → integrations → testing → deployment.**

This order minimizes rework and ensures that every later feature is built on a validated CodeSense core.