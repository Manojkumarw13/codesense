from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.core.database import get_db
from backend.app.core.exceptions import DatabaseError

router = APIRouter()

@router.get("/health")
def get_health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        raise DatabaseError(message=f"Database connection failed: {str(e)}")

