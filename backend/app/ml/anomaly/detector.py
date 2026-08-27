"""ML Anomaly Detection using Isolation Forest - Phase 14."""
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

import joblib
import pandas as pd
from sqlalchemy.orm import Session

from backend.app.core.settings import settings
from backend.app.models.analytics import Anomaly, MetricDefinition
from backend.app.models.configuration import ModelRegistry
from backend.app.models.ml import MLFeatureVector

logger = logging.getLogger("codesense.ml.anomaly")


class MLAnomalyDetector:
    """Detects multivariate anomalies using trained IsolationForest models."""

    def __init__(self, db: Session):
        self.db = db
        # Resolve models dir same as trainer
        self.models_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            settings.ML_MODELS_PATH,
        )

    def _load_active_model(self, team_id: uuid.UUID | None = None) -> tuple[Any, ModelRegistry | None]:
        """Load active model for team, fallback to global.

        Returns (sklearn_model, registry_entry) or (None, None) if not found.
        """
        registry_entry = None
        # Prefer team-specific model if exists
        if team_id:
            registry_entry = (
                self.db.query(ModelRegistry)
                .filter(
                    ModelRegistry.model_name == "team_anomaly",
                    ModelRegistry.team_id == team_id,
                    ModelRegistry.is_active == True,  # noqa: E712
                )
                .order_by(ModelRegistry.created_at.desc())
                .first()
            )
        # Fallback to global
        if not registry_entry:
            registry_entry = (
                self.db.query(ModelRegistry)
                .filter(
                    ModelRegistry.model_name == "global_anomaly",
                    ModelRegistry.is_active == True,  # noqa: E712
                )
                .order_by(ModelRegistry.created_at.desc())
                .first()
            )
        if not registry_entry:
            logger.warning("No active anomaly model found (team=%s)", team_id)
            return None, None

        # Load joblib model
        try:
            model_path = registry_entry.file_path
            # Support both absolute and relative paths
            if not os.path.exists(model_path):
                # Try resolving relative to project root / backend/app
                alt = os.path.join(self.models_dir, os.path.basename(model_path))
                if os.path.exists(alt):
                    model_path = alt
                else:
                    logger.error("Model file not found: %s", registry_entry.file_path)
                    return None, None
            model = joblib.load(model_path)
            return model, registry_entry
        except Exception as e:
            logger.error("Failed to load model %s: %s", registry_entry.file_path, e)
            return None, None

    def _prepare_features(self, features: dict[str, Any], expected_columns: list[str] | None = None) -> pd.DataFrame:
        """Convert feature dict to DataFrame row aligned to expected columns."""
        flat: dict[str, float] = {}
        for key, val in features.items():
            if isinstance(val, dict):
                # For health dimensions stored as dict, use score
                flat[key] = float(val.get("score", 0.0))
            else:
                try:
                    flat[key] = float(val)
                except Exception:
                    flat[key] = 0.0

        if expected_columns:
            # Align strictly to training columns, missing -> median (0)
            row = {col: flat.get(col, 0.0) for col in expected_columns}
            return pd.DataFrame([row], columns=expected_columns)
        # No expected columns: sorted keys for determinism
        cols = sorted(flat.keys())
        row = {col: flat[col] for col in cols}
        return pd.DataFrame([row], columns=cols)

    def _resolve_expected_columns(self, registry: ModelRegistry, fallback_df: pd.DataFrame) -> list[str]:
        """Extract expected feature columns from registry metadata."""
        if registry:
            # Prefer stored feature list in metrics or hyperparameters
            for src in (registry.metrics, registry.hyperparameters):
                if isinstance(src, dict) and "feature_columns" in src:
                    cols = src["feature_columns"]
                    if isinstance(cols, list) and cols:
                        return cols
            # Fallback: infer from file's model n_features_in_
        return list(fallback_df.columns)

    def detect_team_anomaly(
        self, team_id: uuid.UUID, period_start: datetime | None = None, period_end: datetime | None = None
    ) -> dict[str, Any] | None:
        """Run ML anomaly detection for latest team feature vector.

        If period filters provided, uses that period's vector; otherwise latest.
        Returns dict with anomaly result or None if insufficient data.
        """
        query = self.db.query(MLFeatureVector).filter(MLFeatureVector.team_id == team_id)
        if period_start and period_end:
            query = query.filter(
                MLFeatureVector.period_start == period_start,
                MLFeatureVector.period_end == period_end,
            )
        vector = query.order_by(MLFeatureVector.period_end.desc()).first()

        if not vector:
            logger.info("No feature vector for team %s", team_id)
            return None

        model, registry = self._load_active_model(team_id)
        if model is None:
            return None

        # Prepare feature row
        # Extract expected columns from registry if available
        flat_features = vector.features
        # First build temporary df to infer columns if needed
        temp_df = self._prepare_features(flat_features, expected_columns=None)

        expected_cols = None
        if registry and registry.metrics and isinstance(registry.metrics, dict):
            expected_cols = registry.metrics.get("feature_columns")
        if not expected_cols and hasattr(model, "feature_names_in_"):
            try:
                expected_cols = list(model.feature_names_in_)
            except Exception:
                expected_cols = None

        # If model was trained with sorted columns stable, expected_cols may not be stored for old models;
        # infer from n_features_in_ matching
        if expected_cols is None and hasattr(model, "n_features_in_"):
            # Use sorted keys truncated/padded to match n_features
            n_feat = int(model.n_features_in_)
            if len(temp_df.columns) != n_feat:
                # For old models, try to use the model's training column order as sorted
                # we will attempt to align by selecting top n_feat sorted columns
                if len(temp_df.columns) > n_feat:
                    expected_cols = sorted(temp_df.columns)[:n_feat]
                else:
                    # pad missing
                    expected_cols = list(temp_df.columns) + [f"pad_{i}" for i in range(n_feat - len(temp_df.columns))]
                    # But then row will have missing pads as 0
                logger.warning(
                    "Column count mismatch (vector=%d vs model=%d) for team %s, using heuristic alignment",
                    len(temp_df.columns),
                    n_feat,
                    team_id,
                )
            else:
                expected_cols = list(temp_df.columns)

        df_row = self._prepare_features(flat_features, expected_columns=expected_cols)

        try:
            # IsolationForest: predict returns -1 for anomaly, 1 for normal
            pred = model.predict(df_row)[0]
            score = float(model.decision_function(df_row)[0])  # higher normal, lower anomaly
            # anomaly_score via score_samples: opposite of decision_function? use negative decision
            raw_score_samples = float(model.score_samples(df_row)[0]) if hasattr(model, "score_samples") else score

            is_anomaly = int(pred) == -1

            # Convert to confidence: map decision_function to 0-1
            # IsolationForest decision_function: negative => anomaly strength
            # Approximate confidence: sigmoid-ish mapping. Threshold ~0 is boundary.
            # If anomaly, confidence high when score very negative. If normal, confidence high when score positive.
            if is_anomaly:
                # score negative, confidence = min(0.95, 0.5 + abs(score)*0.5) capped
                confidence = min(0.95, 0.55 + abs(score) * 0.4)
                # also factor raw_score_samples if very low
                confidence = max(0.60, confidence)
            else:
                # normal: confidence based on positive score
                confidence = min(0.90, 0.55 + max(0.0, score) * 0.3)
                confidence = max(0.50, confidence)

            # Evidence: which metrics contributed most? Simple heuristic: top deviating features from median
            # Compute deviation by comparing feature value to training median (we don't have median stored, so use z-like)
            # For now, rank features by absolute value (larger values => more likely outlier driver) - simplistic but explainable
            # Better: compute per-feature distance from median approximated as deviation from mean 0? We sort by abs value
            contributions: dict[str, float] = {}
            for col in df_row.columns:
                val = float(df_row.iloc[0][col])
                # Use absolute value weighted
                contributions[col] = abs(val)

            # Top 3 contributors
            top_evidence = dict(sorted(contributions.items(), key=lambda x: x[1], reverse=True)[:5])

            evidence = {
                "ml_anomaly_score": round(score, 4),
                "raw_score_samples": round(raw_score_samples, 4),
                "prediction": int(pred),
                "is_anomaly": bool(is_anomaly),
                "model_name": registry.model_name if registry else "unknown",
                "model_version": registry.version if registry else "unknown",
                "top_contributors": top_evidence,
                "feature_count": len(df_row.columns),
                "period_start": vector.period_start.isoformat() if vector.period_start else None,
                "period_end": vector.period_end.isoformat() if vector.period_end else None,
            }

            severity = "LOW"
            if is_anomaly:
                # Map confidence + score magnitude to severity
                if confidence > 0.85 or score < -0.3:
                    severity = "CRITICAL" if confidence > 0.90 else "HIGH"
                elif confidence > 0.75:
                    severity = "MEDIUM"
                else:
                    severity = "LOW"

            return {
                "team_id": str(team_id),
                "is_anomaly": bool(is_anomaly),
                "anomaly_score": round(score, 4),
                "confidence": round(float(confidence), 3),
                "severity": severity if is_anomaly else "NONE",
                "evidence": evidence,
                "detected_at": datetime.now(timezone.utc).isoformat(),
                "vector_id": str(vector.id),
                "model_id": str(registry.id) if registry else None,
            }

        except Exception as e:
            logger.error("ML anomaly detection failed for team %s: %s", team_id, e, exc_info=True)
            return None

    def detect_and_store(
        self, team_id: uuid.UUID, period_start: datetime, period_end: datetime
    ) -> list[Anomaly]:
        """Detect and persist ML anomalies as Anomaly records when is_anomaly."""
        result = self.detect_team_anomaly(team_id, period_start, period_end)
        if not result or not result.get("is_anomaly"):
            return []

        # Resolve team for org mapping
        from backend.app.models.core import Team
        from backend.app.models.analytics import MetricDefinition

        team = self.db.query(Team).get(team_id)
        if not team:
            return []

        # ML anomalies are multivariate, not tied to single metric.
        # We attach to a synthetic metric or first matching metric_definition for FK compliance.
        # Prefer a generic metric_definition: pick first available or create fallback handling.
        # For storage, we need valid metric_id; use first metric_def if exists else create temporary?
        metric = self.db.query(MetricDefinition).first()
        if not metric:
            logger.warning("No MetricDefinition available for ML anomaly storage")
            return []

        now = datetime.now(timezone.utc)
        anomaly = Anomaly(
            id=uuid.uuid4(),
            organization_id=team.organization_id,
            team_id=team_id,
            metric_id=metric.id,
            severity=result["severity"],
            baseline_value=None,
            observed_value=result["anomaly_score"],
            change_percent=None,
            confidence=result["confidence"],
            evidence=result["evidence"],
            detected_at=now,
        )
        self.db.add(anomaly)
        self.db.commit()
        return [anomaly]
