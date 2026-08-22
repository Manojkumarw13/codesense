import logging
from typing import Generic, TypeVar
from sqlalchemy.orm import Session

logger = logging.getLogger("codesense.services")

class BaseService:
    """Base class for all business logic services."""
    def __init__(self, db: Session) -> None:
        self.db = db
