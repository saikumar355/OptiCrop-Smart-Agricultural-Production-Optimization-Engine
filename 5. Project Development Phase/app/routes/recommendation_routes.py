from flask import Blueprint, render_template, current_app, jsonify
from app.extensions import limiter

recommend_bp = Blueprint('recommend_bp', __name__)


@recommend_bp.route('/recommend', methods=['GET'])
def recommend_page():
    return render_template('recommend.html')


def get_recommend_limit():
    return current_app.config.get('RECOMMEND_RATE_LIMIT', '20 per minute')


@recommend_bp.route('/api/recommend', methods=['POST'])
@limiter.limit(get_recommend_limit)
def api_recommend():
    from app.controllers.recommendation_controller import RecommendationController
    from app.services.recommendation_service import RecommendationService

    engine = current_app.extensions.get('prediction_engine')
    if engine is None:
        return jsonify({'error': 'model_unavailable',
                        'message': 'No model is loaded. Run the training pipeline first.'}), 503

    repo = current_app.extensions['prediction_repository']
    service = RecommendationService(engine, repo)
    controller = RecommendationController(service)
    return controller.handle_recommend()
