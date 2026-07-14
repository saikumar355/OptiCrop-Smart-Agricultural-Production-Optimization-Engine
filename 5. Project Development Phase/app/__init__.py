import os
import sys
import logging
from flask import Flask, request, jsonify, render_template

from app.config import DevelopmentConfig, ProductionConfig
from app.extensions import csrf, limiter
from app.utils.logger import get_logger
from app.utils.correlation_id import generate_correlation_id

def create_app():
    app = Flask(__name__)

    flask_env = os.environ.get('FLASK_ENV')
    if flask_env == 'development':
        app.config.from_object(DevelopmentConfig)
    else:
        app.config.from_object(ProductionConfig)
        if not flask_env:
            logging.warning("FLASK_ENV not set, defaulting to ProductionConfig.")

    # Reload SUITABILITY_THRESHOLDS at runtime in case config class was
    # imported before load_dotenv() ran (Flask reloader edge case).
    if not app.config.get('SUITABILITY_THRESHOLDS'):
        import json as _json
        _thresh_str = os.environ.get('SUITABILITY_THRESHOLDS', '{}')
        try:
            app.config['SUITABILITY_THRESHOLDS'] = _json.loads(_thresh_str)
        except Exception:
            app.config['SUITABILITY_THRESHOLDS'] = {}

    # Initialize logger (pass resolved config values so it doesn't read at import time)
    logger = get_logger(
        __name__,
        log_level=app.config.get('LOG_LEVEL', 'INFO'),
        log_path=app.config.get('LOG_PATH', 'logs/opticrop.log'),
    )

    # Validate required config keys
    required_keys = [
        'SECRET_KEY', 'CSRF_SECRET_KEY',
        'ACTIVE_MODEL_PATH', 'ACTIVE_SCALER_PATH',
        'ADMIN_USERNAME', 'ADMIN_PASSWORD_HASH',
    ]
    missing_keys = [k for k in required_keys if not app.config.get(k)]
    if missing_keys:
        logger.error(f"Missing required configuration variables: {', '.join(missing_keys)}")
        sys.exit(1)

    # Create required directories at startup
    os.makedirs(app.config.get('MODEL_REGISTRY_PATH', 'saved_models/'), exist_ok=True)
    db_path = app.config.get('DATABASE_PATH', 'instance/opticrop.db')
    if db_path != ':memory:':
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
    log_path = app.config.get('LOG_PATH', 'logs/opticrop.log')
    log_dir = os.path.dirname(log_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    os.makedirs(app.config.get('EDA_STATIC_DIR', 'app/static/eda/'), exist_ok=True)

    # ── Initialize the PredictionEngine ONCE at startup ──────────────────────
    # Loading from disk on every request is O(model_size) overhead per call.
    # Store the singleton on app.extensions so routes can retrieve it cheaply.
    model_path = app.config.get('ACTIVE_MODEL_PATH')
    scaler_path = app.config.get('ACTIVE_SCALER_PATH')
    prediction_engine = None
    if os.path.exists(model_path) and os.path.exists(scaler_path):
        try:
            from app.ml.prediction_engine import PredictionEngine
            prediction_engine = PredictionEngine(model_path, scaler_path)
            logger.info(f"PredictionEngine loaded: {model_path}")
        except Exception as exc:
            logger.warning(f"Failed to load PredictionEngine at startup: {exc}")
    else:
        logger.warning(
            f"Model artifact(s) missing at startup — "
            f"model={model_path}, scaler={scaler_path}. "
            "Non-prediction routes will still be served."
        )
    app.extensions['prediction_engine'] = prediction_engine

    # ── Shared PredictionRepository singleton ────────────────────────────────
    from app.repositories.prediction_repository import PredictionRepository
    app.extensions['prediction_repository'] = PredictionRepository(db_path)

    # Initialize extensions
    csrf.init_app(app)
    limiter.init_app(app)

    # Inject config into all Jinja2 templates
    @app.context_processor
    def inject_globals():
        return dict(config=app.config)

    # Register blueprints
    from app.routes.main_routes import main_bp
    app.register_blueprint(main_bp)

    from app.routes.recommendation_routes import recommend_bp
    app.register_blueprint(recommend_bp)

    from app.routes.suitability_routes import suitability_bp
    app.register_blueprint(suitability_bp)

    from app.routes.history_routes import history_bp
    app.register_blueprint(history_bp)

    from app.routes.dashboard_routes import dashboard_bp
    app.register_blueprint(dashboard_bp)

    from app.routes.analytics_routes import analytics_bp
    app.register_blueprint(analytics_bp)

    from app.routes.admin_routes import admin_bp
    app.register_blueprint(admin_bp)

    @app.before_request
    def log_request_info():
        logger.info(f"Request: {request.method} {request.path}")

    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'not_found'}), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        correlation_id = generate_correlation_id()
        logger.error(f"Internal Error 500 (Correlation ID: {correlation_id}): {error}")
        if request.path.startswith('/api/'):
            return jsonify({'error': 'internal_error', 'correlation_id': correlation_id}), 500
        return render_template('errors/500.html', correlation_id=correlation_id), 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        correlation_id = generate_correlation_id()
        logger.error(f"Unhandled Exception (Correlation ID: {correlation_id}): {e}")
        if request.path.startswith('/api/'):
            return jsonify({'error': 'internal_error', 'correlation_id': correlation_id}), 500
        return render_template('errors/500.html', correlation_id=correlation_id), 500

    return app
