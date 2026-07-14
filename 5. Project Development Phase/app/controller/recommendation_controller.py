import logging
from flask import request, jsonify
from app.validators.input_validator import InputValidator, ValidationError
from app.services.recommendation_service import RecommendationService
from app.utils.correlation_id import generate_correlation_id

logger = logging.getLogger(__name__)

class RecommendationController:
    def __init__(self, service: RecommendationService) -> None:
        self.service = service
        
    def handle_recommend(self):
        try:
            data = request.get_json() or {}
        except Exception:
            data = {}
            
        validation_result = InputValidator.validate(data)
        
        if isinstance(validation_result, ValidationError):
            return jsonify({
                "error": "validation_error",
                "fields": validation_result.fields
            }), 400
            
        try:
            from app.utils.hashing import sha256_ip
            hashed_ip = sha256_ip(request.remote_addr or "")

            result, model_name = self.service.recommend(validation_result, hashed_ip)

            return jsonify({
                "predicted_crop": result.predicted_label,
                "confidence_score": round(result.confidence_score, 3),
                "model_name": model_name,
            }), 200
            
        except Exception as e:
            correlation_id = generate_correlation_id()
            logger.error(f"Prediction engine or repository error (Correlation ID: {correlation_id}): {e}")
            return jsonify({
                "error": "internal_error",
                "correlation_id": correlation_id
            }), 500
