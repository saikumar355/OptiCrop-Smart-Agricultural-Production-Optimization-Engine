import logging
from flask import jsonify
from app.services.dashboard_service import DashboardService
from app.utils.correlation_id import generate_correlation_id

logger = logging.getLogger(__name__)

class DashboardController:
    def __init__(self, service: DashboardService) -> None:
        self.service = service
        
    def handle_dashboard(self):
        try:
            stats = self.service.get_dashboard_stats()
            return jsonify(stats), 200
        except Exception as e:
            correlation_id = generate_correlation_id()
            logger.error(f"Dashboard fetch error (Correlation ID: {correlation_id}): {e}")
            return jsonify({
                "error": "internal_error",
                "correlation_id": correlation_id
            }), 500
