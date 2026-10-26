import uuid
from datetime import datetime, timezone

from backend.app.core.database import SessionLocal
from backend.app.models.core import (
    Build,
    CanonicalEvent,
    Change,
    Deployment,
    Incident,
    Organization,
    Review,
    WorkItem,
)
from backend.app.models.raw import ProviderEvent
from backend.app.normalization.github import GitHubNormalizer
from backend.app.normalization.gitlab import GitLabNormalizer
from backend.app.normalization.jira import JiraNormalizer
from backend.app.normalization.simulator import SimulatorNormalizer


def _raw_event(
    db, provider, external_event_id, event_type, payload, source="simulator"
):
    row = ProviderEvent(
        provider=provider,
        external_event_id=external_event_id,
        event_type=event_type,
        payload=payload,
        source=source,
        processing_status="PENDING",
    )
    db.add(row)
    db.flush()
    return row


def _now():
    return datetime.now(timezone.utc)


def test_github_normalizer_creates_canonical_event_with_org_only():
    db = SessionLocal()
    try:
        evt = _raw_event(
            db,
            "github",
            f"gh-{uuid.uuid4().hex[:8]}",
            "pull_request.opened",
            {"action": "opened"},
        )
        GitHubNormalizer(db).normalize(evt)
        canon = db.query(CanonicalEvent).filter_by(raw_event_id=evt.id).first()
        assert canon is not None
        assert canon.organization_id is not None
        assert canon.team_id is None
        org = db.query(Organization).filter_by(external_id="github").first()
        assert org is not None
        assert canon.organization_id == org.id
    finally:
        db.rollback()
        db.close()


def test_gitlab_normalizer_creates_canonical_event_with_org_only():
    db = SessionLocal()
    try:
        evt = _raw_event(
            db, "gitlab", f"gl-{uuid.uuid4().hex[:8]}", "merge_request.created", {}
        )
        GitLabNormalizer(db).normalize(evt)
        canon = db.query(CanonicalEvent).filter_by(raw_event_id=evt.id).first()
        assert canon is not None
        assert canon.organization_id is not None
        assert canon.team_id is None
        org = db.query(Organization).filter_by(external_id="gitlab").first()
        assert org is not None
    finally:
        db.rollback()
        db.close()


def test_jira_normalizer_does_not_raise():
    db = SessionLocal()
    try:
        evt = _raw_event(db, "jira", f"jr-{uuid.uuid4().hex[:8]}", "issue:created", {})
        JiraNormalizer(db).normalize(evt)  # placeholder: logs only
        # Should not crash; no core entities expected from placeholder.
    finally:
        db.rollback()
        db.close()


def test_simulator_work_item_created_persists_work_item_and_canonical():
    db = SessionLocal()
    try:
        wi_id = f"wi-{uuid.uuid4().hex[:8]}"
        payload = {
            "organization_external_id": "sim-org",
            "organization_name": "Sim Org",
            "team_external_id": "sim-team",
            "team_name": "Sim Team",
            "project_external_id": "sim-proj",
            "project_name": "Sim Proj",
            "repository_external_id": "sim-repo",
            "repository_name": "Sim Repo",
            "work_item_id": wi_id,
            "item_type": "FEATURE",
            "title": "Build Normalizer",
            "status": "BACKLOG",
            "priority": "HIGH",
            "actor_ref": "norm@codesense.io",
        }
        evt = _raw_event(
            db, "simulator", f"evt-{uuid.uuid4().hex[:8]}", "WORK_ITEM_CREATED", payload
        )
        SimulatorNormalizer(db).normalize(evt)

        wi = (
            db.query(WorkItem)
            .filter_by(provider="simulator", external_id=wi_id)
            .first()
        )
        assert wi is not None
        assert wi.item_type == "FEATURE"
        assert wi.status == "BACKLOG"

        canon = db.query(CanonicalEvent).filter_by(raw_event_id=evt.id).first()
        assert canon is not None
        assert canon.event_type == "WORK_ITEM_CREATED"
        assert canon.entity_type == "work_item"
        assert canon.entity_id == str(wi.id)
        assert canon.actor_ref == "norm@codesense.io"

        org = db.query(Organization).filter_by(external_id="sim-org").first()
        assert org is not None
        assert canon.organization_id == org.id
    finally:
        db.rollback()
        db.close()


def test_simulator_change_merged_sets_merged_at():
    db = SessionLocal()
    try:
        change_id = f"ch-{uuid.uuid4().hex[:8]}"
        base = {
            "organization_external_id": "sim-org",
            "organization_name": "Sim Org",
            "team_external_id": "sim-team",
            "team_name": "Sim Team",
            "project_external_id": "sim-proj",
            "project_name": "Sim Proj",
            "repository_external_id": "sim-repo",
            "repository_name": "Sim Repo",
        }
        # Create the change first (open, merged_at is None on create path).
        ch_evt = _raw_event(
            db,
            "simulator",
            f"evt-{uuid.uuid4().hex[:8]}",
            "CHANGE_CREATED",
            {**base, "change_id": change_id, "title": "C", "status": "OPEN"},
        )
        SimulatorNormalizer(db).normalize(ch_evt)

        # Then merge it -> merged_at is set on the update path.
        m_evt = _raw_event(
            db,
            "simulator",
            f"evt-{uuid.uuid4().hex[:8]}",
            "CHANGE_MERGED",
            {**base, "change_id": change_id, "title": "C", "status": "MERGED"},
        )
        SimulatorNormalizer(db).normalize(m_evt)

        ch = (
            db.query(Change)
            .filter_by(provider="simulator", external_id=change_id)
            .first()
        )
        assert ch is not None
        assert ch.status == "MERGED"
        assert ch.merged_at is not None

        canon = db.query(CanonicalEvent).filter_by(raw_event_id=m_evt.id).first()
        assert canon.entity_type == "change"
    finally:
        db.rollback()
        db.close()


def test_simulator_review_completed_sets_completed_at():
    db = SessionLocal()
    try:
        # Need a change to attach the review to
        change_id = f"ch-{uuid.uuid4().hex[:8]}"
        rev_id = f"rev-{uuid.uuid4().hex[:8]}"
        base = {
            "organization_external_id": "sim-org",
            "organization_name": "Sim Org",
            "team_external_id": "sim-team",
            "team_name": "Sim Team",
            "project_external_id": "sim-proj",
            "project_name": "Sim Proj",
            "repository_external_id": "sim-repo",
            "repository_name": "Sim Repo",
        }
        # Create the change first
        ch_evt = _raw_event(
            db,
            "simulator",
            f"evt-{uuid.uuid4().hex[:8]}",
            "CHANGE_CREATED",
            {**base, "change_id": change_id, "title": "C"},
        )
        SimulatorNormalizer(db).normalize(ch_evt)

        # Request a review (creates PENDING review, requested_at set, completed_at None).
        req_evt = _raw_event(
            db,
            "simulator",
            f"evt-{uuid.uuid4().hex[:8]}",
            "REVIEW_REQUESTED",
            {**base, "review_id": rev_id, "change_id": change_id, "status": "PENDING"},
        )
        SimulatorNormalizer(db).normalize(req_evt)

        # Then complete it -> update path sets completed_at.
        rev_evt = _raw_event(
            db,
            "simulator",
            f"evt-{uuid.uuid4().hex[:8]}",
            "REVIEW_COMPLETED",
            {**base, "review_id": rev_id, "change_id": change_id, "status": "APPROVED"},
        )
        SimulatorNormalizer(db).normalize(rev_evt)

        rev = (
            db.query(Review).filter_by(provider="simulator", external_id=rev_id).first()
        )
        assert rev is not None
        assert rev.status == "APPROVED"
        assert rev.completed_at is not None
    finally:
        db.rollback()
        db.close()


def test_simulator_build_completed_sets_duration():
    db = SessionLocal()
    try:
        build_id = f"build-{uuid.uuid4().hex[:8]}"
        base = {
            "organization_external_id": "sim-org",
            "organization_name": "Sim Org",
            "team_external_id": "sim-team",
            "team_name": "Sim Team",
            "project_external_id": "sim-proj",
            "project_name": "Sim Proj",
            "repository_external_id": "sim-repo",
            "repository_name": "Sim Repo",
        }
        # Create the build first (started_at set, completed_at None on create path).
        start_evt = _raw_event(
            db,
            "simulator",
            f"evt-{uuid.uuid4().hex[:8]}",
            "BUILD_STARTED",
            {**base, "build_id": build_id, "status": "RUNNING"},
        )
        SimulatorNormalizer(db).normalize(start_evt)

        # Then complete it -> update path sets completed_at + duration.
        evt = _raw_event(
            db,
            "simulator",
            f"evt-{uuid.uuid4().hex[:8]}",
            "BUILD_COMPLETED",
            {
                **base,
                "build_id": build_id,
                "status": "SUCCESS",
                "duration_seconds": 120,
            },
        )
        SimulatorNormalizer(db).normalize(evt)

        b = (
            db.query(Build)
            .filter_by(provider="simulator", external_id=build_id)
            .first()
        )
        assert b is not None
        assert b.status == "SUCCESS"
        assert b.completed_at is not None
        assert b.duration_seconds == 120
    finally:
        db.rollback()
        db.close()


def test_simulator_deployment_failed_and_incident_resolved():
    db = SessionLocal()
    try:
        base = {
            "organization_external_id": "sim-org",
            "organization_name": "Sim Org",
            "team_external_id": "sim-team",
            "team_name": "Sim Team",
            "project_external_id": "sim-proj",
            "project_name": "Sim Proj",
            "repository_external_id": "sim-repo",
            "repository_name": "Sim Repo",
        }
        dep_evt = _raw_event(
            db,
            "simulator",
            f"evt-{uuid.uuid4().hex[:8]}",
            "DEPLOYMENT_STARTED",
            {**base, "deployment_id": "dep-1", "status": "RUNNING"},
        )
        SimulatorNormalizer(db).normalize(dep_evt)
        # Transition to failed -> update path sets completed_at.
        dep_evt = _raw_event(
            db,
            "simulator",
            f"evt-{uuid.uuid4().hex[:8]}",
            "DEPLOYMENT_FAILED",
            {**base, "deployment_id": "dep-1", "status": "FAILED"},
        )
        SimulatorNormalizer(db).normalize(dep_evt)
        d = (
            db.query(Deployment)
            .filter_by(provider="simulator", external_id="dep-1")
            .first()
        )
        assert d is not None
        assert d.status == "FAILED"
        assert d.completed_at is not None

        # Create the incident first (resolved_at None on create path).
        inc_evt = _raw_event(
            db,
            "simulator",
            f"evt-{uuid.uuid4().hex[:8]}",
            "INCIDENT_CREATED",
            {
                **base,
                "incident_id": "inc-1",
                "title": "Spike",
                "severity": "SEV2",
                "status": "OPEN",
            },
        )
        SimulatorNormalizer(db).normalize(inc_evt)
        # Then resolve it -> update path sets resolved_at.
        inc_evt = _raw_event(
            db,
            "simulator",
            f"evt-{uuid.uuid4().hex[:8]}",
            "INCIDENT_RESOLVED",
            {
                **base,
                "incident_id": "inc-1",
                "title": "Spike",
                "severity": "SEV2",
                "status": "RESOLVED",
            },
        )
        SimulatorNormalizer(db).normalize(inc_evt)
        inc = (
            db.query(Incident)
            .filter_by(provider="simulator", external_id="inc-1")
            .first()
        )
        assert inc is not None
        assert inc.status == "RESOLVED"
        assert inc.resolved_at is not None
    finally:
        db.rollback()
        db.close()


def test_simulator_normalization_is_idempotent_for_work_item():
    db = SessionLocal()
    try:
        wi_id = f"wi-{uuid.uuid4().hex[:8]}"
        base = {
            "organization_external_id": "sim-org",
            "organization_name": "Sim Org",
            "team_external_id": "sim-team",
            "team_name": "Sim Team",
            "project_external_id": "sim-proj",
            "project_name": "Sim Proj",
            "repository_external_id": "sim-repo",
            "repository_name": "Sim Repo",
            "work_item_id": wi_id,
            "item_type": "TASK",
            "title": "T",
            "status": "BACKLOG",
        }
        evt1 = _raw_event(
            db, "simulator", f"evt-{uuid.uuid4().hex[:8]}", "WORK_ITEM_CREATED", base
        )
        evt2 = _raw_event(
            db, "simulator", f"evt-{uuid.uuid4().hex[:8]}", "WORK_ITEM_CREATED", base
        )
        SimulatorNormalizer(db).normalize(evt1)
        SimulatorNormalizer(db).normalize(evt2)

        count = (
            db.query(WorkItem)
            .filter_by(provider="simulator", external_id=wi_id)
            .count()
        )
        assert count == 1
        canons = (
            db.query(CanonicalEvent)
            .filter(CanonicalEvent.raw_event_id.in_([evt1.id, evt2.id]))
            .count()
        )
        assert canons == 2
    finally:
        db.rollback()
        db.close()
