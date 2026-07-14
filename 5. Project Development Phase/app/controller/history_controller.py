import logging
from flask import request, jsonify
from app.repositories.prediction_repository import PredictionRepository
from app.utils.correlation_id import generate_correlation_id

logger = logging.getLogger(__name__)

class HistoryController:
    def __init__(self, repo: PredictionRepository) -> None:
        self.repo = repo
        
    def handle_history(self):
        try:
            page = int(request.args.get('page', 1))
            page_size = int(request.args.get('page_size', 25))
            
            if page < 1:
                page = 1
            if page_size < 1:
                page_size = 25
            if page_size > 100:
                page_size = 100
                
            records = self.repo.get_paginated(page, page_size)
            total = self.repo.count()
            
            response_records = []
            for r in records:
                response_records.append({
                    "id": r.id,
                    "timestamp": r.timestamp,
                    "N": r.N,
                    "P": r.P,
                    "K": r.K,
                    "temperature": r.temperature,
                    "humidity": r.humidity,
                    "rainfall": r.rainfall,
                    "ph": r.ph,
                    "predicted_crop": r.predicted_crop,
                    "confidence_score": round(r.confidence_score, 3),
                    "model_name": r.model_name
                })
                
            return jsonify({
                "records": response_records,
                "total": total,
                "page": page,
                "page_size": page_size
            }), 200
            
        except ValueError:
            return jsonify({
                "error": "invalid_parameters",
                "message": "page and page_size must be integers"
            }), 400
        except Exception as e:
            correlation_id = generate_correlation_id()
            logger.error(f"History fetch error (Correlation ID: {correlation_id}): {e}")
            return jsonify({
                "error": "internal_error",
                "correlation_id": correlation_id
            }), 500
