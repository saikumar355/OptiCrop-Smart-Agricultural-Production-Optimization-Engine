import pytest
import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set required env vars before any imports touch them.
os.environ.setdefault('FLASK_ENV', 'development')
os.environ.setdefault('SECRET_KEY', 'test_secret_key')
os.environ.setdefault('CSRF_SECRET_KEY', 'test_csrf_secret')
os.environ.setdefault('ADMIN_USERNAME', 'admin')
os.environ.setdefault('ADMIN_PASSWORD_HASH', '$2b$12$placeholderhashabcdefghijklmnopqrstuvwxyzABCDE')
os.environ.setdefault('ACTIVE_MODEL_PATH', 'saved_models/ExtraTrees_2026-07-01T122126Z.pkl')
os.environ.setdefault('ACTIVE_SCALER_PATH', 'saved_models/scaler_2026-07-01T122126Z.pkl')
os.environ.setdefault('DATABASE_PATH', ':memory:')

from app.models.prediction_result import PredictionResult


def _make_mock_engine(predicted_label='rice', confidence=0.95):
    """Return a MagicMock that behaves like a PredictionEngine singleton."""
    mock = MagicMock()
    mock.model_name = 'ExtraTrees_2026-07-01T122126Z'
    mock.predict.return_value = PredictionResult(
        predicted_label=predicted_label,
        confidence_score=confidence,
    )
    return mock


@pytest.fixture
def app():
    """
    Flask test app with:
    - CSRF disabled
    - In-memory SQLite
    - PredictionEngine stubbed out (avoids loading real .pkl at test time)
    """
    mock_engine = _make_mock_engine()

    # Patch PredictionEngine.__init__ so create_app() doesn't touch the real
    # .pkl files — those are runtime artifacts, not committed test fixtures.
    with patch('app.ml.prediction_engine.PredictionEngine') as MockEngineClass:
        MockEngineClass.return_value = mock_engine
        # Also patch os.path.exists so the startup path-check passes
        with patch('os.path.exists', return_value=True):
            from app import create_app
            _app = create_app()

    _app.config['TESTING'] = True
    _app.config['WTF_CSRF_ENABLED'] = False
    _app.config['DATABASE_PATH'] = ':memory:'

    # Replace the engine singleton with our mock so route handlers use it.
    _app.extensions['prediction_engine'] = mock_engine

    return _app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def mock_engine(app):
    """
    Expose the mock PredictionEngine already stored on app.extensions so
    individual tests can assert on it or override its return value.
    """
    return app.extensions['prediction_engine']


@pytest.fixture
def repo(app):
    """Expose the in-memory PredictionRepository singleton."""
    return app.extensions['prediction_repository']
