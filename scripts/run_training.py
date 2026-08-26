import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.core.database import SessionLocal
from backend.app.ml.training.trainer import ModelTrainer

def run_training():
    db = SessionLocal()
    try:
        trainer = ModelTrainer(db)
        print("Training global model...")
        global_model = trainer.train_global_model()
        print(f"Global model trained: {global_model.version}")
        
        print("Training team models...")
        team_models = trainer.train_team_models()
        print(f"Trained {len(team_models)} team models.")
    finally:
        db.close()

if __name__ == "__main__":
    run_training()
