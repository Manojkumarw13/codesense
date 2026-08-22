import hashlib
import json
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from backend.app.core.database import get_db
from backend.app.models.raw import ProviderEvent
from backend.app.schemas.event import ProviderEventCreate, ProviderEventResponse
from backend.app.core.exceptions import ConflictError, ValidationError

router = APIRouter()
logger = logging.getLogger("codesense.ingestion")
quarantine_logger = logging.getLogger("codesense.quarantine")

def compute_payload_hash(payload: Dict[str, Any]) -> str:
    """Computes SHA-256 hash of the sorted JSON payload."""
    serialized = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()


@router.post("/events", status_code=status.HTTP_201_CREATED)
def ingest_event(event_in: ProviderEventCreate, db: Session = Depends(get_db)):
    """Ingests a single raw provider event."""
    try:
        # Check if event already exists (deduplication)
        existing = db.query(ProviderEvent).filter_by(
            provider=event_in.provider,
            external_event_id=event_in.external_event_id
        ).first()
        
        if existing:
            # Idempotent response: return status 200 or 201 but indicate duplicate
            return {
                "status": "ignored_duplicate",
                "id": str(existing.id),
                "provider": existing.provider,
                "external_event_id": existing.external_event_id
            }

        payload_hash = compute_payload_hash(event_in.payload)
        
        db_obj = ProviderEvent(
            provider=event_in.provider,
            external_event_id=event_in.external_event_id,
            event_type=event_in.event_type,
            event_timestamp=event_in.event_timestamp,
            payload=event_in.payload,
            payload_hash=payload_hash,
            source=event_in.source,
            processing_status="PENDING"
        )
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        return {
            "status": "ingested",
            "id": str(db_obj.id),
            "provider": db_obj.provider,
            "external_event_id": db_obj.external_event_id
        }
        
    except IntegrityError as e:
        db.rollback()
        # Fallback deduplication handling in case of race conditions
        existing = db.query(ProviderEvent).filter_by(
            provider=event_in.provider,
            external_event_id=event_in.external_event_id
        ).first()
        if existing:
            return {
                "status": "ignored_duplicate",
                "id": str(existing.id),
                "provider": existing.provider,
                "external_event_id": existing.external_event_id
            }
        raise ConflictError(message=f"Integrity violation during ingestion: {str(e)}")
        
    except Exception as e:
        db.rollback()
        # Log to quarantine
        quarantine_logger.error(
            f"Failed to ingest event: {event_in.model_dump_json()} - Error: {str(e)}"
        )
        raise e


@router.post("/events/batch", status_code=status.HTTP_201_CREATED)
def ingest_events_batch(events_in: List[ProviderEventCreate], db: Session = Depends(get_db)):
    """Ingests a batch of raw provider events."""
    results = []
    
    # Process events one-by-one to support partial success and individual deduplication
    for event_in in events_in:
        try:
            # Check if event already exists (deduplication)
            existing = db.query(ProviderEvent).filter_by(
                provider=event_in.provider,
                external_event_id=event_in.external_event_id
            ).first()
            
            if existing:
                results.append({
                    "status": "ignored_duplicate",
                    "id": str(existing.id),
                    "provider": existing.provider,
                    "external_event_id": existing.external_event_id
                })
                continue

            payload_hash = compute_payload_hash(event_in.payload)
            
            db_obj = ProviderEvent(
                provider=event_in.provider,
                external_event_id=event_in.external_event_id,
                event_type=event_in.event_type,
                event_timestamp=event_in.event_timestamp,
                payload=event_in.payload,
                payload_hash=payload_hash,
                source=event_in.source,
                processing_status="PENDING"
            )
            
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            
            results.append({
                "status": "ingested",
                "id": str(db_obj.id),
                "provider": db_obj.provider,
                "external_event_id": db_obj.external_event_id
            })
            
        except IntegrityError:
            db.rollback()
            existing = db.query(ProviderEvent).filter_by(
                provider=event_in.provider,
                external_event_id=event_in.external_event_id
            ).first()
            if existing:
                results.append({
                    "status": "ignored_duplicate",
                    "id": str(existing.id),
                    "provider": existing.provider,
                    "external_event_id": existing.external_event_id
                })
            else:
                results.append({
                    "status": "failed",
                    "provider": event_in.provider,
                    "external_event_id": event_in.external_event_id,
                    "reason": "IntegrityError"
                })
        except Exception as e:
            db.rollback()
            quarantine_logger.error(
                f"Failed to ingest event in batch: {event_in.model_dump_json()} - Error: {str(e)}"
            )
            results.append({
                "status": "failed",
                "provider": event_in.provider,
                "external_event_id": event_in.external_event_id,
                "reason": str(e)
            })
            
    return {"ingested_count": len([r for r in results if r["status"] == "ingested"]), "results": results}


@router.get("/events")
def list_raw_events(
    provider: Optional[str] = Query(None, description="Filter by provider"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    processing_status: Optional[str] = Query(None, description="Filter by processing status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Retrieves list of raw provider events with pagination and filters."""
    query = db.query(ProviderEvent)
    
    if provider:
        query = query.filter(ProviderEvent.provider == provider)
    if event_type:
        query = query.filter(ProviderEvent.event_type == event_type)
    if processing_status:
        query = query.filter(ProviderEvent.processing_status == processing_status)
        
    total = query.count()
    events = query.order_by(ProviderEvent.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": events
    }
