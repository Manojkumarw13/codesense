from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

class ProviderEventCreate(BaseModel):
    provider: str = Field(..., description="Name of the external provider (e.g., github, simulator)")
    external_event_id: str = Field(..., description="Unique event identifier from the provider")
    event_type: str = Field(..., description="Type of event (e.g., CHANGE_CREATED, WORK_ITEM_STARTED)")
    event_timestamp: Optional[datetime] = Field(None, description="Original timestamp when the event occurred on the provider")
    payload: Dict[str, Any] = Field(..., description="Raw provider event payload")
    source: str = Field(..., description="Source of event ingestion (e.g., webhook, api, simulator)")

    @field_validator("provider", "external_event_id", "event_type", "source")
    @classmethod
    def check_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace only")
        return v.strip()


class ProviderEventResponse(BaseModel):
    id: Any
    provider: str
    external_event_id: str
    event_type: str
    received_at: datetime
    event_timestamp: Optional[datetime]
    payload: Dict[str, Any]
    payload_hash: Optional[str]
    source: str
    processing_status: str
    processed_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
