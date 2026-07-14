"""
Tests for POST /api/suitability
"""
import pytest

VALID_PAYLOAD = {
    "N": 90,
    "P": 42,
    "K": 43,
    "temperature": 20.8,
    "humidity": 82,
    "rainfall": 202.9,
    "ph": 6.5,
}


def test_suitability_valid_payload_returns_200(client):
    """A valid input vector returns 200 with suitable, marginal, unsuitable keys."""
    resp = client.post('/api/suitability', json=VALID_PAYLOAD)
    assert resp.status_code == 200

    data = resp.get_json()
    assert 'suitable' in data
    assert 'marginal' in data
    assert 'unsuitable' in data

    # All three values must be lists
    assert isinstance(data['suitable'], list)
    assert isinstance(data['marginal'], list)
    assert isinstance(data['unsuitable'], list)


def test_suitability_empty_thresholds_returns_empty_lists(client):
    """With SUITABILITY_THRESHOLDS={} (default in tests) all lists are empty."""
    resp = client.post('/api/suitability', json=VALID_PAYLOAD)
    assert resp.status_code == 200

    data = resp.get_json()
    # No thresholds configured → no crops evaluated → all lists empty
    assert data['suitable'] == []
    assert data['marginal'] == []
    assert data['unsuitable'] == []


def test_suitability_missing_field_returns_400(client):
    """Omitting 'K' should produce a 400 with validation_error and 'K' in fields."""
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != 'K'}
    resp = client.post('/api/suitability', json=payload)
    assert resp.status_code == 400

    data = resp.get_json()
    assert data['error'] == 'validation_error'
    assert 'fields' in data
    assert 'K' in data['fields']


def test_suitability_out_of_range_humidity_returns_400(client):
    """humidity=200 is outside [0, 100]; should produce a 400 with a field-level error."""
    payload = {**VALID_PAYLOAD, 'humidity': 200}
    resp = client.post('/api/suitability', json=payload)
    assert resp.status_code == 400

    data = resp.get_json()
    assert data['error'] == 'validation_error'
    assert 'humidity' in data['fields']
