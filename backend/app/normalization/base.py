import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from backend.app.models.raw import ProviderEvent
from backend.app.models.core import Organization, Team, Project, Repository, CanonicalEvent

logger = logging.getLogger("codesense.normalization")

class BaseNormalizer(ABC):
    """Abstract base class for all provider event normalizers."""
    def __init__(self, db: Session) -> None:
        self.db = db

    @abstractmethod
    def normalize(self, raw_event: ProviderEvent) -> None:
        """Processes a raw event, resolving entities and creating canonical events."""
        pass

    def get_or_create_organization(self, external_id: str, name: str) -> Organization:
        """Helper to resolve or create an Organization by external ID."""
        org = self.db.query(Organization).filter_by(external_id=external_id).first()
        if not org:
            org = Organization(
                external_id=external_id,
                name=name,
                slug=external_id.lower().replace("_", "-")[:100]
            )
            self.db.add(org)
            self.db.flush()
        return org

    def get_or_create_team(self, org_id: Any, external_id: str, name: str) -> Team:
        """Helper to resolve or create a Team by external ID."""
        team = self.db.query(Team).filter_by(organization_id=org_id, external_id=external_id).first()
        if not team:
            team = Team(
                organization_id=org_id,
                external_id=external_id,
                name=name
            )
            self.db.add(team)
            self.db.flush()
        return team

    def get_or_create_project(self, org_id: Any, team_id: Any, external_id: str, name: str) -> Project:
        """Helper to resolve or create a Project by external ID."""
        project = self.db.query(Project).filter_by(organization_id=org_id, external_id=external_id).first()
        if not project:
            project = Project(
                organization_id=org_id,
                team_id=team_id,
                external_id=external_id,
                name=name
            )
            self.db.add(project)
            self.db.flush()
        return project

    def get_or_create_repository(self, team_id: Any, project_id: Optional[Any], provider: str, external_id: str, name: str) -> Repository:
        """Helper to resolve or create a Repository by external ID."""
        repo = self.db.query(Repository).filter_by(provider=provider, external_id=external_id).first()
        if not repo:
            repo = Repository(
                team_id=team_id,
                project_id=project_id,
                provider=provider,
                external_id=external_id,
                name=name
            )
            self.db.add(repo)
            self.db.flush()
        return repo

    def create_canonical_event(
        self,
        raw_event: ProviderEvent,
        org_id: Any,
        team_id: Optional[Any],
        project_id: Optional[Any],
        repo_id: Optional[Any],
        event_type: str,
        occurred_at: Any,
        actor_ref: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CanonicalEvent:
        """Helper to create and save a CanonicalEvent."""
        canonical_event = CanonicalEvent(
            raw_event_id=raw_event.id,
            organization_id=org_id,
            team_id=team_id,
            project_id=project_id,
            repository_id=repo_id,
            event_type=event_type,
            occurred_at=occurred_at,
            actor_ref=actor_ref,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_json=metadata or {}
        )
        self.db.add(canonical_event)
        self.db.flush()
        return canonical_event
