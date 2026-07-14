import logging
from flask import jsonify
from app.services.analytics_service import AnalyticsService
from app.utils.correlation_id import generate_correlation_id

logger = logging.getLogger(__name__)

class AnalyticsController:
    def __init__(self, service: AnalyticsService) -> None:
        self.service = service
        
    def handle_analytics(self):
        try:
            stats = self.service.get_analytics()
            return jsonify(stats), 200
        except Exception as e:
            correlation_id = generate_correlation_id()
            logger.error(f"Analytics fetch error (Correlation ID: {correlation_id}): {e}")
            return jsonify({
                "error": "internal_error",
                "correlation_id": correlation_id
            }), 500
