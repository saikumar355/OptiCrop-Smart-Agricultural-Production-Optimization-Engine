"""
Tests for GET /api/history
"""
import pytest


def test_history_empty_db_returns_expected_structure(client):
    """Empty database returns records=[], total=0, page=1, page_size=25."""
    resp = client.get('/api/history')
    assert resp.status_code == 200

    data = resp.get_json()
    assert data['records'] == []
    assert data['total'] == 0
    assert data['page'] == 1
    assert data['page_size'] == 25


def test_history_pagination_params_are_reflected(client):
    """Query params page=1&page_size=5 are echoed back in the response."""
    resp = client.get('/api/history?page=1&page_size=5')
    assert resp.status_code == 200

    data = resp.get_json()
    assert data['page'] == 1
    assert data['page_size'] == 5
    assert isinstance(data['records'], list)
    assert 'total' in data


def test_history_records_do_not_contain_hashed_ip(client, app):
    """Records returned to the client must never include the hashed_ip field."""
    from unittest.mock import MagicMock
    from app.models.prediction_record import PredictionRecord

    fake_record = PredictionRecord(
        id=1,
        timestamp='2024-01-15T10:30:00Z',
        N=90.0, P=42.0, K=43.0,
        temperature=20.8, humidity=82.0, rainfall=202.9, ph=6.5,
        predicted_crop='rice',
        confidence_score=0.95,
        model_name='TestModel',
        hashed_ip='abc123deadbeef' * 4,
    )

    # Swap the singleton repo on app.extensions with a mock
    mock_repo = MagicMock()
    mock_repo.get_paginated.return_value = [fake_record]
    mock_repo.count.return_value = 1
    original_repo = app.extensions['prediction_repository']
    app.extensions['prediction_repository'] = mock_repo

    try:
        resp = client.get('/api/history')
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data['records']) == 1
        record = data['records'][0]
        assert 'hashed_ip' not in record
        assert record['predicted_crop'] == 'rice'
        assert record['id'] == 1
    finally:
        app.extensions['prediction_repository'] = original_repo
