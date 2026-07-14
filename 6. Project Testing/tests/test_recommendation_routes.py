"""
Tests for POST /api/recommend
"""
import pytest
from app.models.prediction_result import PredictionResult


VALID_PAYLOAD = {
    "N": 90,
    "P": 42,
    "K": 43,
    "temperature": 20.8,
    "humidity": 82,
    "rainfall": 202.9,
    "ph": 6.5,
}


def test_recommend_valid_payload_returns_200(client, mock_engine):
    """A valid input vector returns 200 with predicted_crop, confidence_score, model_name."""
    resp = client.post('/api/recommend', json=VALID_PAYLOAD)
    assert resp.status_code == 200

    data = resp.get_json()
    assert 'predicted_crop' in data
    assert 'confidence_score' in data
    assert 'model_name' in data
    assert data['predicted_crop'] == 'rice'
    assert data['confidence_score'] == pytest.approx(0.95, abs=1e-3)


def test_recommend_model_name_is_real_not_hardcoded(client, mock_engine):
    """model_name in the response must come from the engine artifact, not 'ActiveModel'."""
    resp = client.post('/api/recommend', json=VALID_PAYLOAD)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['model_name'] != 'ActiveModel'
    assert data['model_name'] == mock_engine.model_name


def test_recommend_missing_field_returns_400(client):
    """Omitting 'N' should produce a 400 with validation_error and 'N' in fields."""
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != 'N'}
    resp = client.post('/api/recommend', json=payload)
    assert resp.status_code == 400

    data = resp.get_json()
    assert data['error'] == 'validation_error'
    assert 'fields' in data
    assert 'N' in data['fields']


def test_recommend_non_numeric_field_returns_400(client):
    """Passing N='abc' should produce a 400 with a field-level error for N."""
    payload = {**VALID_PAYLOAD, 'N': 'abc'}
    resp = client.post('/api/recommend', json=payload)
    assert resp.status_code == 400

    data = resp.get_json()
    assert data['error'] == 'validation_error'
    assert 'N' in data['fields']


def test_recommend_out_of_range_value_returns_400(client):
    """N=999 is outside [0, 140]; should produce a 400 with a field-level error for N."""
    payload = {**VALID_PAYLOAD, 'N': 999}
    resp = client.post('/api/recommend', json=payload)
    assert resp.status_code == 400

    data = resp.get_json()
    assert data['error'] == 'validation_error'
    assert 'N' in data['fields']


@pytest.mark.parametrize("field", ['N', 'P', 'K', 'temperature', 'humidity', 'rainfall', 'ph'])
def test_recommend_each_field_missing_returns_400(client, field):
    """Each of the 7 fields individually missing returns 400 with that field in errors."""
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != field}
    resp = client.post('/api/recommend', json=payload)
    assert resp.status_code == 400
    assert field in resp.get_json()['fields']


def test_recommend_engine_called_once(client, mock_engine):
    """The engine predict() must be called exactly once per valid request."""
    client.post('/api/recommend', json=VALID_PAYLOAD)
    mock_engine.predict.assert_called_once()


def test_recommend_no_engine_returns_503(app, client):
    """If no model is loaded (engine=None), the endpoint returns 503."""
    app.extensions['prediction_engine'] = None
    resp = client.post('/api/recommend', json=VALID_PAYLOAD)
    assert resp.status_code == 503
    # Restore for other tests
    from unittest.mock import MagicMock
    from app.models.prediction_result import PredictionResult
    mock = MagicMock()
    mock.model_name = 'ExtraTrees_2026-07-01T122126Z'
    mock.predict.return_value = PredictionResult(predicted_label='rice', confidence_score=0.95)
    app.extensions['prediction_engine'] = mock
