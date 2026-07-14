import os
import json
import logging
from typing import Dict, Any

from app.repositories.prediction_repository import PredictionRepository

logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(self, repo: PredictionRepository, config) -> None:
        self.repo = repo
        self.registry_path = getattr(config, 'MODEL_REGISTRY_PATH', 'saved_models/')

    def get_analytics(self) -> Dict[str, Any]:
        """
        Return analytics data.  Aggregate queries are delegated to the
        repository — no page-fetching of raw records in this service.
        """
        # 1. Model scores from metadata.json
        model_scores = []
        metadata_file = os.path.join(self.registry_path, 'metadata.json')
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r') as f:
                    meta = json.load(f)
                model_scores.append({
                    "model": meta.get("model_name", "Unknown"),
                    "f1_weighted": meta.get("f1_weighted", 0.0),
                })
            except Exception as e:
                logger.error(f"Failed to read metadata.json: {e}")

        # 2. Daily volumes and crop distribution via SQL aggregations
        daily_volumes = self.repo.daily_counts(days=90)
        crop_distribution = self.repo.crop_distribution()

        return {
            "model_scores": model_scores,
            "daily_volumes": daily_volumes,
            "crop_distribution": crop_distribution,
        }
