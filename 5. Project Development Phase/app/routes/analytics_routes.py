from flask import Blueprint, render_template, current_app
from app.controllers.analytics_controller import AnalyticsController
from app.services.analytics_service import AnalyticsService

analytics_bp = Blueprint('analytics_bp', __name__)


@analytics_bp.route('/analytics', methods=['GET'])
def analytics_page():
    return render_template('analytics.html')


@analytics_bp.route('/api/analytics', methods=['GET'])
def api_analytics():
    repo = current_app.extensions['prediction_repository']
    service = AnalyticsService(repo, current_app.config)
    controller = AnalyticsController(service)
    return controller.handle_analytics()
