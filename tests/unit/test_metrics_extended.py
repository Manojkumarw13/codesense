import uuid
from datetime import datetime, timedelta, timezone

from backend.app.core.database import SessionLocal
from backend.app.models.core import (
    Build,
    Change,
    Deployment,
    Incident,
    Organization,
    Project,
    Repository,
    Review,
    Team,
    WorkItem,
)
from backend.app.services.metrics import MetricEngine


def _setup_team(db):
    org_id = uuid.uuid4()
    team_id = uuid.uuid4()
    proj_id = uuid.uuid4()
    repo_id = uuid.uuid4()
    org = Organization(id=org_id, name="Metrics Org")
    team = Team(id=team_id, name="Metrics Team", organization_id=org_id)
    db.add(org)
    db.add(team)
    db.flush()  # team must exist before project/repository reference it
    project = Project(
        id=proj_id, organization_id=org_id, team_id=team_id, name="Metrics Project"
    )
    repository = Repository(
        id=repo_id,
        team_id=team_id,
        project_id=proj_id,
        provider="simulator",
        external_id=f"repo-{uuid.uuid4().hex[:8]}",
        name="Metrics Repo",
    )
    db.add(project)
    db.add(repository)
    db.commit()
    return org_id, team_id, proj_id, repo_id


def _period(days_back=7):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days_back)
    return start, end


def _engine(db):
    return MetricEngine(db)


def _value_for(values, engine, key):
    return next(v for v in values if engine.metric_defs[key].id == v.metric_id)


def test_deployment_frequency_counts_successful_deployments():
    db = SessionLocal()
    try:
        _, team_id, _, repo_id = _setup_team(db)
        start, end = _period()
        for i in range(4):
            db.add(
                Deployment(
                    id=uuid.uuid4(),
                    team_id=team_id,
                    repository_id=repo_id,
                    provider="github",
                    external_id=f"dep-{i}-{uuid.uuid4().hex[:8]}",
                    status="SUCCESS",
                    completed_at=start + timedelta(days=i),
                )
            )
        db.add(
            Deployment(
                id=uuid.uuid4(),
                team_id=team_id,
                repository_id=repo_id,
                provider="github",
                external_id=f"dep-fail-{uuid.uuid4().hex[:8]}",
                status="FAILURE",
                completed_at=start + timedelta(days=5),
            )
        )
        db.commit()

        engine = _engine(db)
        values = engine.calculate_metrics_for_period(team_id, start, end)
        df = _value_for(values, engine, "deployment_frequency")
        assert df.value == 4.0
    finally:
        db.rollback()
        db.close()


def test_deployment_failure_rate_is_percentage():
    db = SessionLocal()
    try:
        _, team_id, _, repo_id = _setup_team(db)
        start, end = _period()
        for i in range(8):
            db.add(
                Deployment(
                    id=uuid.uuid4(),
                    team_id=team_id,
                    repository_id=repo_id,
                    provider="github",
                    external_id=f"dep-{i}-{uuid.uuid4().hex[:8]}",
                    status="SUCCESS",
                    completed_at=start + timedelta(hours=i),
                )
            )
        for i in range(2):
            db.add(
                Deployment(
                    id=uuid.uuid4(),
                    team_id=team_id,
                    repository_id=repo_id,
                    provider="github",
                    external_id=f"dep-fail-{i}-{uuid.uuid4().hex[:8]}",
                    status="FAILURE",
                    completed_at=start + timedelta(hours=10 + i),
                )
            )
        db.commit()

        engine = _engine(db)
        values = engine.calculate_metrics_for_period(team_id, start, end)
        dfr = _value_for(values, engine, "deployment_failure_rate")
        assert dfr.value == 20.0
    finally:
        db.rollback()
        db.close()


def test_build_success_rate_is_percentage():
    db = SessionLocal()
    try:
        _, team_id, _, repo_id = _setup_team(db)
        start, end = _period()
        for i in range(9):
            db.add(
                Build(
                    id=uuid.uuid4(),
                    team_id=team_id,
                    repository_id=repo_id,
                    provider="simulator",
                    external_id=f"build-{i}-{uuid.uuid4().hex[:8]}",
                    status="SUCCESS",
                    started_at=start,
                    completed_at=start + timedelta(minutes=5),
                )
            )
        db.add(
            Build(
                id=uuid.uuid4(),
                team_id=team_id,
                repository_id=repo_id,
                provider="simulator",
                external_id=f"build-fail-{uuid.uuid4().hex[:8]}",
                status="FAILED",
                started_at=start,
                completed_at=start + timedelta(minutes=5),
            )
        )
        db.commit()

        engine = _engine(db)
        values = engine.calculate_metrics_for_period(team_id, start, end)
        bsr = _value_for(values, engine, "build_success_rate")
        assert bsr.value == 90.0
    finally:
        db.rollback()
        db.close()


def test_lead_time_from_change_to_deployment():
    db = SessionLocal()
    try:
        _, team_id, _, repo_id = _setup_team(db)
        start, end = _period()
        created = start + timedelta(days=1)
        completed = start + timedelta(days=2)
        change = Change(
            id=uuid.uuid4(),
            team_id=team_id,
            repository_id=repo_id,
            provider="github",
            external_id=f"ch-{uuid.uuid4().hex[:8]}",
            title="C",
            status="MERGED",
            created_at=created,
            merged_at=completed,
        )
        db.add(change)
        db.add(
            Deployment(
                id=uuid.uuid4(),
                team_id=team_id,
                repository_id=repo_id,
                change_id=change.id,
                provider="github",
                external_id=f"dep-{uuid.uuid4().hex[:8]}",
                status="SUCCESS",
                completed_at=completed,
            )
        )
        db.commit()

        engine = _engine(db)
        values = engine.calculate_metrics_for_period(team_id, start, end)
        lt = _value_for(values, engine, "lead_time")
        assert abs(lt.value - 86400.0) < 1
    finally:
        db.rollback()
        db.close()


def test_cycle_time_from_work_item():
    db = SessionLocal()
    try:
        _, team_id, proj_id, repo_id = _setup_team(db)
        start, end = _period()
        started = start + timedelta(days=1)
        completed = start + timedelta(days=2)
        for i in range(2):
            db.add(
                WorkItem(
                    id=uuid.uuid4(),
                    team_id=team_id,
                    project_id=proj_id,
                    repository_id=repo_id,
                    provider="simulator",
                    external_id=f"wi-{i}-{uuid.uuid4().hex[:8]}",
                    item_type="FEATURE",
                    title=f"WI {i}",
                    status="COMPLETED",
                    started_at=started,
                    completed_at=completed,
                )
            )
        db.commit()

        engine = _engine(db)
        values = engine.calculate_metrics_for_period(team_id, start, end)
        ct = _value_for(values, engine, "cycle_time")
        assert abs(ct.value - 86400.0) < 1
    finally:
        db.rollback()
        db.close()


def test_pr_cycle_time_from_change():
    db = SessionLocal()
    try:
        _, team_id, _, repo_id = _setup_team(db)
        start, end = _period()
        created = start + timedelta(days=1)
        merged = start + timedelta(days=3)
        for i in range(2):
            db.add(
                Change(
                    id=uuid.uuid4(),
                    team_id=team_id,
                    repository_id=repo_id,
                    provider="github",
                    external_id=f"ch-{i}-{uuid.uuid4().hex[:8]}",
                    title=f"C {i}",
                    status="MERGED",
                    created_at=created,
                    merged_at=merged,
                )
            )
        db.commit()

        engine = _engine(db)
        values = engine.calculate_metrics_for_period(team_id, start, end)
        pr = _value_for(values, engine, "pr_cycle_time")
        assert abs(pr.value - 172800.0) < 1
    finally:
        db.rollback()
        db.close()


def test_review_turnaround_from_review():
    db = SessionLocal()
    try:
        _, team_id, _, repo_id = _setup_team(db)
        start, end = _period()
        change = Change(
            id=uuid.uuid4(),
            team_id=team_id,
            repository_id=repo_id,
            provider="github",
            external_id=f"ch-{uuid.uuid4().hex[:8]}",
            title="C",
            status="MERGED",
        )
        db.add(change)
        db.flush()
        requested = start + timedelta(days=1)
        completed = start + timedelta(days=2)
        db.add(
            Review(
                id=uuid.uuid4(),
                change_id=change.id,
                provider="github",
                external_id=f"rev-{uuid.uuid4().hex[:8]}",
                reviewer_reference="alice",
                status="APPROVED",
                requested_at=requested,
                completed_at=completed,
            )
        )
        db.commit()

        engine = _engine(db)
        values = engine.calculate_metrics_for_period(team_id, start, end)
        rt = _value_for(values, engine, "review_turnaround")
        assert abs(rt.value - 86400.0) < 1
    finally:
        db.rollback()
        db.close()


def test_review_backlog_counts_pending_reviews():
    db = SessionLocal()
    try:
        _, team_id, _, repo_id = _setup_team(db)
        start, end = _period()
        change = Change(
            id=uuid.uuid4(),
            team_id=team_id,
            repository_id=repo_id,
            provider="github",
            external_id=f"ch-{uuid.uuid4().hex[:8]}",
            title="C",
            status="OPEN",
        )
        db.add(change)
        db.flush()
        for i in range(3):
            db.add(
                Review(
                    id=uuid.uuid4(),
                    change_id=change.id,
                    provider="github",
                    external_id=f"rev-{i}-{uuid.uuid4().hex[:8]}",
                    status="PENDING",
                    requested_at=start + timedelta(hours=i),
                )
            )
        db.commit()

        engine = _engine(db)
        values = engine.calculate_metrics_for_period(team_id, start, end)
        rb = _value_for(values, engine, "review_backlog")
        assert rb.value == 3.0
    finally:
        db.rollback()
        db.close()


def test_pipeline_duration_from_builds():
    db = SessionLocal()
    try:
        _, team_id, _, repo_id = _setup_team(db)
        start, end = _period()
        for i in range(2):
            db.add(
                Build(
                    id=uuid.uuid4(),
                    team_id=team_id,
                    repository_id=repo_id,
                    provider="simulator",
                    external_id=f"build-{i}-{uuid.uuid4().hex[:8]}",
                    status="SUCCESS",
                    started_at=start,
                    completed_at=start + timedelta(minutes=10),
                )
            )
        db.commit()

        engine = _engine(db)
        values = engine.calculate_metrics_for_period(team_id, start, end)
        pd = _value_for(values, engine, "pipeline_duration")
        assert abs(pd.value - 600.0) < 1
    finally:
        db.rollback()
        db.close()


def test_change_failure_rate_from_incidents():
    db = SessionLocal()
    try:
        _, team_id, _, repo_id = _setup_team(db)
        start, end = _period()
        for i in range(4):
            db.add(
                Deployment(
                    id=uuid.uuid4(),
                    team_id=team_id,
                    repository_id=repo_id,
                    provider="github",
                    external_id=f"dep-{i}-{uuid.uuid4().hex[:8]}",
                    status="SUCCESS",
                    completed_at=start + timedelta(hours=i),
                )
            )
        for i in range(2):
            db.add(
                Incident(
                    id=uuid.uuid4(),
                    team_id=team_id,
                    repository_id=repo_id,
                    provider="github",
                    external_id=f"inc-{i}-{uuid.uuid4().hex[:8]}",
                    title=f"Inc {i}",
                    severity="SEV2",
                    status="RESOLVED",
                    created_at=start + timedelta(hours=i),
                )
            )
        db.commit()

        engine = _engine(db)
        values = engine.calculate_metrics_for_period(team_id, start, end)
        cfr = _value_for(values, engine, "change_failure_rate")
        assert cfr.value == 50.0
    finally:
        db.rollback()
        db.close()


def test_mttr_from_incidents():
    db = SessionLocal()
    try:
        _, team_id, _, repo_id = _setup_team(db)
        start, end = _period()
        created = start + timedelta(days=1)
        resolved = start + timedelta(days=3)
        for i in range(2):
            db.add(
                Incident(
                    id=uuid.uuid4(),
                    team_id=team_id,
                    repository_id=repo_id,
                    provider="github",
                    external_id=f"inc-{i}-{uuid.uuid4().hex[:8]}",
                    title=f"Inc {i}",
                    severity="SEV2",
                    status="RESOLVED",
                    created_at=created,
                    resolved_at=resolved,
                )
            )
        db.commit()

        engine = _engine(db)
        values = engine.calculate_metrics_for_period(team_id, start, end)
        mttr = _value_for(values, engine, "mttr")
        assert abs(mttr.value - 172800.0) < 1
    finally:
        db.rollback()
        db.close()


def test_work_in_progress_counts_inflight_work_items():
    db = SessionLocal()
    try:
        _, team_id, proj_id, repo_id = _setup_team(db)
        start, end = _period()
        started = start - timedelta(days=1)
        for i in range(2):
            db.add(
                WorkItem(
                    id=uuid.uuid4(),
                    team_id=team_id,
                    project_id=proj_id,
                    repository_id=repo_id,
                    provider="simulator",
                    external_id=f"wi-{i}-{uuid.uuid4().hex[:8]}",
                    item_type="FEATURE",
                    title=f"WI {i}",
                    status="IN_PROGRESS",
                    started_at=started,
                )
            )
        db.add(
            WorkItem(
                id=uuid.uuid4(),
                team_id=team_id,
                project_id=proj_id,
                repository_id=repo_id,
                provider="simulator",
                external_id=f"wi-done-{uuid.uuid4().hex[:8]}",
                item_type="FEATURE",
                title="Done",
                status="COMPLETED",
                started_at=started,
                completed_at=start + timedelta(hours=1),
            )
        )
        db.commit()

        engine = _engine(db)
        values = engine.calculate_metrics_for_period(team_id, start, end)
        wip = _value_for(values, engine, "work_in_progress")
        assert wip.value == 2.0
    finally:
        db.rollback()
        db.close()


def test_empty_period_still_emits_zero_valued_metrics():
    db = SessionLocal()
    try:
        _, team_id, _, _ = _setup_team(db)
        start, end = _period()
        db.commit()

        engine = _engine(db)
        values = engine.calculate_metrics_for_period(team_id, start, end)
        df = _value_for(values, engine, "deployment_frequency")
        assert df.value == 0.0
        rb = _value_for(values, engine, "review_backlog")
        assert rb.value == 0.0
        wip = _value_for(values, engine, "work_in_progress")
        assert wip.value == 0.0
    finally:
        db.rollback()
        db.close()


def test_change_percentage_computed_when_previous_period_exists():
    db = SessionLocal()
    try:
        _, team_id, _, repo_id = _setup_team(db)
        now = datetime.now(timezone.utc)
        p_start = now - timedelta(days=14)
        p_end = now - timedelta(days=7)
        c_start = now - timedelta(days=7)
        c_end = now

        for i in range(2):
            db.add(
                Deployment(
                    id=uuid.uuid4(),
                    team_id=team_id,
                    repository_id=repo_id,
                    provider="github",
                    external_id=f"dep-p-{i}-{uuid.uuid4().hex[:8]}",
                    status="SUCCESS",
                    completed_at=p_start + timedelta(hours=i),
                )
            )
        for i in range(6):
            db.add(
                Deployment(
                    id=uuid.uuid4(),
                    team_id=team_id,
                    repository_id=repo_id,
                    provider="github",
                    external_id=f"dep-c-{i}-{uuid.uuid4().hex[:8]}",
                    status="SUCCESS",
                    completed_at=c_start + timedelta(hours=i),
                )
            )
        db.commit()

        engine = _engine(db)
        engine.calculate_metrics_for_period(team_id, p_start, p_end)
        values = engine.calculate_metrics_for_period(team_id, c_start, c_end)
        df = _value_for(values, engine, "deployment_frequency")
        assert df.value == 6.0
        assert df.baseline_value == 2.0
        assert abs(df.change_percentage - 200.0) < 1
    finally:
        db.rollback()
        db.close()
