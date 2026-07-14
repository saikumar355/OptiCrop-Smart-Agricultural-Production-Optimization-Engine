from flask import Blueprint, render_template, current_app
from app.controllers.dashboard_controller import DashboardController
from app.services.dashboard_service import DashboardService

dashboard_bp = Blueprint('dashboard_bp', __name__)


@dashboard_bp.route('/dashboard', methods=['GET'])
def dashboard_page():
    return render_template('dashboard.html')


@dashboard_bp.route('/api/dashboard', methods=['GET'])
def api_dashboard():
    repo = current_app.extensions['prediction_repository']
    service = DashboardService(repo)
    controller = DashboardController(service)
    return controller.handle_dashboard()
