import os
import json
import time
import logging
import threading
import subprocess
from typing import Dict, Any

from app.models.model_metadata import ModelMetadata
from app.repositories.prediction_repository import PredictionRepository

logger = logging.getLogger(__name__)

class AdminService:
    def __init__(self, repo: PredictionRepository, config) -> None:
        self.repo = repo
        self.registry_path = getattr(config, 'MODEL_REGISTRY_PATH', 'saved_models/')
        self.db_path = getattr(config, 'DATABASE_PATH', 'instance/opticrop.db')
        self.start_time = time.time()
        
    def get_model_metadata(self) -> ModelMetadata:
        metadata_file = os.path.join(self.registry_path, 'metadata.json')
        if not os.path.exists(metadata_file):
            return ModelMetadata("None", 0.0, "N/A", "N/A", "N/A")
            
        try:
            with open(metadata_file, 'r') as f:
                meta = json.load(f)
                return ModelMetadata(
                    model_name=meta.get("model_name", "Unknown"),
                    f1_weighted=meta.get("f1_weighted", 0.0),
                    serialization_timestamp=meta.get("serialization_timestamp", "N/A"),
                    model_path=meta.get("model_path", "N/A"),
                    scaler_path=meta.get("scaler_path", "N/A")
                )
        except Exception as e:
            logger.error(f"Failed to read metadata: {e}")
            return ModelMetadata("Error", 0.0, "Error", "Error", "Error")
            
    def get_system_health(self) -> Dict[str, Any]:
        uptime_seconds = int(time.time() - self.start_time)
        count = self.repo.count()
        
        db_size_mb = 0.0
        if os.path.exists(self.db_path):
            db_size_mb = os.path.getsize(self.db_path) / (1024 * 1024)
            
        status = self.get_retrain_status()
        
        return {
            "uptime_seconds": uptime_seconds,
            "total_predictions": count,
            "db_size_mb": round(db_size_mb, 2),
            "last_training_timestamp": status.get("timestamp", "Never")
        }
        
    def get_retrain_status(self) -> Dict[str, str]:
        status_file = os.path.join(self.registry_path, 'training_status.json')
        if not os.path.exists(status_file):
            return {"status": "none", "timestamp": "N/A"}
            
        try:
            with open(status_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read retrain status: {e}")
            return {"status": "error", "timestamp": "N/A"}
            
    def trigger_retraining(self) -> None:
        def run_script():
            try:
                # Update status to in-progress
                os.makedirs(self.registry_path, exist_ok=True)
                status_file = os.path.join(self.registry_path, 'training_status.json')
                with open(status_file, 'w') as f:
                    json.dump({"status": "in_progress", "timestamp": "N/A"}, f)
                    
                result = subprocess.run(["python", "scripts/train.py"], capture_output=True, text=True)
                if result.returncode != 0:
                    logger.error(f"Retraining script failed with return code {result.returncode}.\nStderr: {result.stderr}")
                    with open(status_file, 'w') as f:
                        json.dump({"status": "failed", "timestamp": "N/A"}, f)
            except Exception as e:
                logger.error(f"Failed to execute retraining script: {e}")
                
        thread = threading.Thread(target=run_script, daemon=True)
        thread.start()
        logger.info("Triggered retraining in background.")
