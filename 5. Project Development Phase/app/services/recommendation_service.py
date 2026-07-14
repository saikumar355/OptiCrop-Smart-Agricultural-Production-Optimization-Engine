import logging
from datetime import datetime, timezone
from typing import Tuple

from app.ml.prediction_engine import PredictionEngine
from app.repositories.prediction_repository import PredictionRepository
from app.models.input_vector import InputVector
from app.models.prediction_result import PredictionResult
from app.models.prediction_record import PredictionRecord

logger = logging.getLogger(__name__)


class RecommendationService:
    def __init__(self, engine: PredictionEngine, repo: PredictionRepository) -> None:
        self.engine = engine
        self.repo = repo

    def recommend(self, input_vector: InputVector, hashed_ip: str) -> Tuple[PredictionResult, str]:
        """
        Invoke the engine, persist the record, and return (result, model_name).
        The model_name is read from the engine artifact, never hardcoded.
        """
        input_list = [
            input_vector.N, input_vector.P, input_vector.K,
            input_vector.temperature, input_vector.humidity,
            input_vector.rainfall, input_vector.ph,
        ]

        result = self.engine.predict(input_list)

        # Use the real model name from the engine artifact filename
        model_name = getattr(self.engine, 'model_name', 'UnknownModel')

        record = PredictionRecord(
            id=None,
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            N=input_vector.N,
            P=input_vector.P,
            K=input_vector.K,
            temperature=input_vector.temperature,
            humidity=input_vector.humidity,
            rainfall=input_vector.rainfall,
            ph=input_vector.ph,
            predicted_crop=result.predicted_label,
            confidence_score=result.confidence_score,
            model_name=model_name,
            hashed_ip=hashed_ip,
        )

        self.repo.save(record)

        logger.info(
            "Recommendation made. Input: N=%.1f P=%.1f K=%.1f temp=%.1f "
            "hum=%.1f rain=%.1f ph=%.2f. Predicted: %s (Confidence: %.2f)",
            input_vector.N, input_vector.P, input_vector.K,
            input_vector.temperature, input_vector.humidity,
            input_vector.rainfall, input_vector.ph,
            result.predicted_label, result.confidence_score,
        )

        return result, model_name
