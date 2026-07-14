import logging
from flask import request, jsonify
from app.validators.input_validator import InputValidator, ValidationError
from app.services.suitability_service import SuitabilityService
from app.utils.correlation_id import generate_correlation_id

logger = logging.getLogger(__name__)

class SuitabilityController:
    def __init__(self, service: SuitabilityService) -> None:
        self.service = service
        
    def handle_suitability(self):
        try:
            data = request.get_json() or {}
        except Exception:
            data = {}

        crop = str(data.get('crop', '')).strip()
        if not crop:
            return jsonify({
                "error": "validation_error",
                "fields": {"crop": "Please select a target crop."}
            }), 400

        validation_result = InputValidator.validate(data)
        
        if isinstance(validation_result, ValidationError):
            return jsonify({
                "error": "validation_error",
                "fields": validation_result.fields
            }), 400
            
        try:
            result = self.service.evaluate_crop(crop, validation_result)
            return jsonify(result), 200
            
        except Exception as e:
            correlation_id = generate_correlation_id()
            logger.error(f"Suitability service error (Correlation ID: {correlation_id}): {e}")
            return jsonify({
                "error": "internal_error",
                "correlation_id": correlation_id
            }), 500
