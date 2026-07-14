"""
Tests for admin routes: /admin, /admin/login, /api/admin/metadata
"""
import pytest


# ---------------------------------------------------------------------------
# Helper: inject an authenticated session
# ---------------------------------------------------------------------------

def _login_session(client):
    """Inject admin_logged_in=True directly into the session cookie."""
    with client.session_transaction() as sess:
        sess['admin_logged_in'] = True


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_admin_dashboard_without_login_redirects(client):
    """GET /admin without a session redirects to /admin/login (302)."""
    resp = client.get('/admin', follow_redirects=False)
    assert resp.status_code == 302
    assert '/admin/login' in resp.headers['Location']


def test_admin_login_page_returns_200(client):
    """GET /admin/login returns 200."""
    resp = client.get('/admin/login')
    assert resp.status_code == 200


def test_admin_login_wrong_credentials_fails(client):
    """POST /admin/login with wrong credentials does NOT set a logged-in session
    and returns a non-200 response (redirect back to login or 401)."""
    resp = client.post(
        '/admin/login',
        data={'username': 'admin', 'password': 'definitely_wrong_password'},
        follow_redirects=False,
    )
    # Controller redirects back to login with 401, or just redirects (302).
    # Either way it must not be a 200 success that grants access.
    assert resp.status_code != 200

    # The session must NOT contain admin_logged_in=True
    with client.session_transaction() as sess:
        assert not sess.get('admin_logged_in')


def test_api_admin_metadata_without_login_redirects(client):
    """GET /api/admin/metadata without a session should redirect (302) to login."""
    resp = client.get('/api/admin/metadata', follow_redirects=False)
    assert resp.status_code == 302
    assert '/admin/login' in resp.headers['Location']


def test_admin_dashboard_with_injected_session_returns_200(client):
    """An authenticated session (injected via session_transaction) can reach /admin."""
    _login_session(client)
    resp = client.get('/admin', follow_redirects=False)
    assert resp.status_code == 200


def test_api_admin_metadata_with_injected_session_returns_200(client, monkeypatch):
    """An authenticated session can reach GET /api/admin/metadata."""
    from unittest.mock import MagicMock
    from app.models.model_metadata import ModelMetadata

    fake_metadata = ModelMetadata(
        model_name='ExtraTrees',
        f1_weighted=0.99,
        serialization_timestamp='2026-07-01T12:21:26Z',
        model_path='saved_models/ExtraTrees_2026-07-01T122126Z.pkl',
        scaler_path='saved_models/scaler_2026-07-01T122126Z.pkl',
    )

    mock_service = MagicMock()
    mock_service.get_model_metadata.return_value = fake_metadata

    # Patch AdminService so the controller gets our mock
    monkeypatch.setattr(
        'app.routes.admin_routes.AdminService',
        lambda *a, **kw: mock_service
    )

    _login_session(client)
    resp = client.get('/api/admin/metadata', follow_redirects=False)
    assert resp.status_code == 200

    data = resp.get_json()
    assert data['model_name'] == 'ExtraTrees'
    assert 'f1_weighted' in data
