from flask import Blueprint, render_template, current_app
from app.controllers.history_controller import HistoryController

history_bp = Blueprint('history_bp', __name__)


@history_bp.route('/history', methods=['GET'])
def history_page():
    return render_template('history.html')


@history_bp.route('/api/history', methods=['GET'])
def api_history():
    repo = current_app.extensions['prediction_repository']
    controller = HistoryController(repo)
    return controller.handle_history()
