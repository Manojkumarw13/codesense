"""Model Training Service."""
import logging
import os
import uuid
from datetime import datetime

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sqlalchemy.orm import Session

from backend.app.core.settings import settings
from backend.app.models.configuration import ModelRegistry
from backend.app.models.ml import MLFeatureVector

logger = logging.getLogger("codesense.ml.training")

class ModelTrainer:
    def __init__(self, db: Session):
        self.db = db
        # Ensure model save directory exists
        self.models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), settings.ML_MODELS_PATH)
        os.makedirs(self.models_dir, exist_ok=True)

    def train_global_model(self) -> ModelRegistry:
        """Train a global anomaly detection model on all available team feature vectors."""
        logger.info("Fetching ML feature vectors from database...")
        vectors = self.db.query(MLFeatureVector).all()
        
        if len(vectors) < 10:
            raise ValueError(f"Not enough data to train global model. Found {len(vectors)} vectors, need at least 10.")
            
        # Prepare DataFrame
        data = []
        for v in vectors:
            row = {"team_id": str(v.team_id)}
            for key, val in v.features.items():
                if isinstance(val, dict):
                    row[key] = val.get("score", 0.0)
                else:
                    row[key] = float(val)
            data.append(row)
            
        df = pd.DataFrame(data)
        
        # Fill missing values with median for now
        numeric_df = df.drop(columns=["team_id"]).fillna(df.drop(columns=["team_id"]).median())
        
        # Ensure deterministic column order (sorted) for reproducible inference
        numeric_df = numeric_df.reindex(sorted(numeric_df.columns), axis=1)
        feature_columns = list(numeric_df.columns)
        
        logger.info(f"Training Isolation Forest on {len(numeric_df)} samples with {len(feature_columns)} features...")
        model = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
        model.fit(numeric_df)
        
        # Save model
        version = f"v{datetime.now().strftime('%Y%m%d%H%M%S')}"
        model_filename = f"global_anomaly_{version}.joblib"
        model_path = os.path.join(self.models_dir, model_filename)
        
        joblib.dump(model, model_path)
        logger.info(f"Model saved to {model_path}")
        
        # Invalidate older models
        self.db.query(ModelRegistry).filter(
            ModelRegistry.model_name == "global_anomaly"
        ).update({"is_active": False})
        
        # Register new model
        registry_entry = ModelRegistry(
            model_name="global_anomaly",
            version=version,
            model_type="isolation_forest",
            description="Global Anomaly Detection Model across all teams",
            file_path=model_path,
            hyperparameters={"n_estimators": 100, "contamination": 0.1, "random_state": 42, "feature_columns": feature_columns},
            metrics={"training_samples": len(numeric_df), "feature_columns": feature_columns, "feature_count": len(feature_columns)},
            is_active=True
        )
        self.db.add(registry_entry)
        self.db.commit()
        
        logger.info("Global model registered successfully.")
        return registry_entry

    def train_team_models(self) -> list[ModelRegistry]:
        """Train team-specific adaptation models."""
        logger.info("Fetching ML feature vectors to train team-specific models...")
        vectors = self.db.query(MLFeatureVector).all()
        
        data = []
        for v in vectors:
            row = {"team_id": str(v.team_id), "org_id": str(v.organization_id)}
            for key, val in v.features.items():
                if isinstance(val, dict):
                    row[key] = val.get("score", 0.0)
                else:
                    row[key] = float(val)
            data.append(row)
            
        df = pd.DataFrame(data)
        
        registered_models = []
        
        if df.empty:
            logger.warning("No data found for team models.")
            return registered_models
            
        for team_id, group in df.groupby("team_id"):
            if len(group) < 5:
                logger.debug(f"Skipping team {team_id} due to insufficient data ({len(group)} samples).")
                continue
                
            org_id = group["org_id"].iloc[0]
            numeric_group = group.drop(columns=["team_id", "org_id"]).fillna(group.drop(columns=["team_id", "org_id"]).median())
            numeric_group = numeric_group.reindex(sorted(numeric_group.columns), axis=1)
            feature_columns_team = list(numeric_group.columns)
            
            # Simple adaptation model (e.g. baseline distribution or simpler tree)
            model = IsolationForest(n_estimators=50, contamination=0.1, random_state=42)
            model.fit(numeric_group)
            
            version = f"v{datetime.now().strftime('%Y%m%d%H%M%S')}"
            model_filename = f"team_{team_id}_anomaly_{version}.joblib"
            model_path = os.path.join(self.models_dir, model_filename)
            
            joblib.dump(model, model_path)
            
            # Invalidate older models for this team
            self.db.query(ModelRegistry).filter(
                ModelRegistry.model_name == "team_anomaly",
                ModelRegistry.team_id == uuid.UUID(team_id)
            ).update({"is_active": False})
            
            registry_entry = ModelRegistry(
                model_name="team_anomaly",
                version=version,
                model_type="isolation_forest",
                description=f"Team-specific Anomaly Detection Model for team {team_id}",
                file_path=model_path,
                hyperparameters={"n_estimators": 50, "contamination": 0.1, "random_state": 42, "feature_columns": feature_columns_team},
                metrics={"training_samples": len(numeric_group), "feature_columns": feature_columns_team, "feature_count": len(feature_columns_team)},
                organization_id=uuid.UUID(org_id),
                team_id=uuid.UUID(team_id),
                is_active=True
            )
            self.db.add(registry_entry)
            registered_models.append(registry_entry)
            
        self.db.commit()
        logger.info(f"Trained {len(registered_models)} team-specific models.")
        return registered_models
