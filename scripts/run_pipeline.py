import os
import sys
from datetime import datetime, timedelta, timezone

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.core.database import SessionLocal
from backend.app.ml.features.pipeline import FeatureExtractor
from backend.app.models.core import Team
from backend.app.services.detection import DetectionEngine
from backend.app.services.health import HealthScoreEngine
from backend.app.services.metrics import MetricEngine


def run_all():
    db = SessionLocal()
    try:
        end_now = datetime.now(timezone.utc)
        
        teams = db.query(Team).all()
        
        metric_agg = MetricEngine(db)
        health_agg = HealthScoreEngine(db)
        try:
            detector = DetectionEngine(db)
        except Exception:
            pass
            
        extractor = FeatureExtractor(db)
        
        # Loop over the past 30 days, day by day
        for day_offset in range(30, -1, -1):
            start = end_now - timedelta(days=day_offset+1)
            end = end_now - timedelta(days=day_offset)
            print(f"\n--- Processing for period {start.date()} to {end.date()} ---")
            
            for team in teams:
                try:
                    metrics = metric_agg.calculate_metrics_for_period(team.id, start, end)
                    db.add_all(metrics)
                    db.commit()
                except Exception:
                    db.rollback()
                    
                try:
                    health = health_agg.calculate_health_score(team.id, start, end)
                    db.add(health)
                    db.commit()
                except Exception:
                    db.rollback()
                    
                try:
                    detector = DetectionEngine(db)
                    detector.run_detection_for_period(team.id, start, end)
                except Exception:
                    db.rollback()
                    
            try:
                count = extractor.run_extraction_for_period(start, end)
                print(f"  Extracted features for {count} teams.")
            except Exception:
                db.rollback()
            
    finally:
        db.close()

if __name__ == "__main__":
    run_all()
