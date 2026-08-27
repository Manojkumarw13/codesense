"""ML API - models, training, features, predictions including ML anomaly detection."""
import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.ml.anomaly.detector import MLAnomalyDetector
from backend.app.ml.features.pipeline import FeatureExtractor
from backend.app.ml.training.trainer import ModelTrainer
from backend.app.models.configuration import ModelRegistry
from backend.app.models.ml import MLFeatureVector

router = APIRouter()


@router.get("/ml/models")
def list_models(
    model_name: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """List registered ML models."""
    q = db.query(ModelRegistry)
    if model_name:
        q = q.filter(ModelRegistry.model_name == model_name)
    if is_active is not None:
        q = q.filter(ModelRegistry.is_active == is_active)
    total = q.count()
    items = q.order_by(ModelRegistry.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.post("/ml/train")
def train_models(
    team_id: Optional[uuid.UUID] = Query(None, description="If provided, train only this team's adaptation; otherwise global"),
    db: Session = Depends(get_db),
):
    """Trigger model training job."""
    trainer = ModelTrainer(db)
    try:
        if team_id:
            # Team-specific training would require sufficient data; fallback to team_models
            models = trainer.train_team_models()
            # Filter for requested team
            filtered = [m for m in models if str(m.team_id) == str(team_id)] if team_id else models
            return {"status": "team_models_trained", "count": len(filtered), "models": filtered}
        else:
            global_model = trainer.train_global_model()
            team_models = trainer.train_team_models()
            return {
                "status": "trained",
                "global_model": global_model,
                "team_models_count": len(team_models),
                "team_models": team_models,
            }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {e}")


@router.get("/ml/features")
def get_features(
    team_id: Optional[uuid.UUID] = Query(None),
    organization_id: Optional[uuid.UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get team feature vectors."""
    q = db.query(MLFeatureVector)
    if team_id:
        q = q.filter(MLFeatureVector.team_id == team_id)
    if organization_id:
        q = q.filter(MLFeatureVector.organization_id == organization_id)
    total = q.count()
    items = q.order_by(MLFeatureVector.calculated_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.get("/ml/predictions")
def get_ml_predictions(
    team_id: uuid.UUID = Query(..., description="Team to predict for"),
    db: Session = Depends(get_db),
):
    """Get ML predictions (risk + anomaly) for a team - unified predictions endpoint."""
    from backend.app.ml.prediction.risk import RiskPredictor

    # Risk
    risk_pred = RiskPredictor(db).predict_team_risk(team_id)

    # Anomaly
    detector = MLAnomalyDetector(db)
    anomaly_pred = detector.detect_team_anomaly(team_id)

    return {
        "team_id": str(team_id),
        "risk": risk_pred,
        "anomaly": anomaly_pred or {"is_anomaly": False, "confidence": 0.0, "detail": "No feature vector or model available"},
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/ml/predictions/anomaly")
def predict_anomaly(
    team_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
):
    """ML anomaly prediction for a specific team (multivariate)."""
    detector = MLAnomalyDetector(db)
    result = detector.detect_team_anomaly(team_id)
    if not result:
        raise HTTPException(status_code=404, detail="No feature vector or active model found for this team")
    return result


@router.get("/ml/predictions/risk")
def predict_risk(team_id: uuid.UUID = Query(...), db: Session = Depends(get_db)):
    """Risk prediction for a team."""
    from backend.app.ml.prediction.risk import RiskPredictor
    from backend.app.models.core import Team

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return RiskPredictor(db).predict_team_risk(team_id)


@router.post("/ml/detect")
def run_ml_detection(
    team_id: uuid.UUID,
    period_start: datetime,
    period_end: datetime,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Run ML anomaly detection for a period and persist if anomalous."""
    detector = MLAnomalyDetector(db)
    result = detector.detect_team_anomaly(team_id, period_start, period_end)
    if not result:
        raise HTTPException(status_code=404, detail="No feature vector or model found")
    persisted = []
    if result.get("is_anomaly"):
        persisted = detector.detect_and_store(team_id, period_start, period_end)
    return {"detection": result, "persisted_count": len(persisted)}


@router.post("/ml/fusion")
def run_fusion(
    team_id: uuid.UUID,
    period_start: datetime,
    period_end: datetime,
    db: Session = Depends(get_db),
):
    """Run Fusion Engine (Rules+Stats+ML) for a team and period."""
    from backend.app.ml.fusion_engine import FusionEngine

    engine = FusionEngine(db)
    result = engine.run_fused_detection(team_id, period_start, period_end)
    return result


@router.get("/ml/fusion/status")
def fusion_status(db: Session = Depends(get_db)):
    """Fusion engine status - shows model readiness."""
    active_global = db.query(ModelRegistry).filter(ModelRegistry.model_name == "global_anomaly", ModelRegistry.is_active == True).count()  # noqa: E712
    active_team = db.query(ModelRegistry).filter(ModelRegistry.model_name == "team_anomaly", ModelRegistry.is_active == True).count()  # noqa: E712
    vectors = db.query(MLFeatureVector).count()
    return {
        "fusion_engine": "ready" if active_global > 0 else "needs_training",
        "active_global_models": active_global,
        "active_team_models": active_team,
        "feature_vectors": vectors,
    }
