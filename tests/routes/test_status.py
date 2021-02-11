"""
test_status.py
Tests the /status API endpoints
"""
from tests import client
from pyconnect.config import get_settings


def test_status_get(settings):
    """
    Tests /status [GET]
    :param settings: Settings test fixture
    """
    client.app.dependency_overrides[get_settings] = lambda: settings
    actual_response = client.get('/status')
    assert actual_response.status_code == 200

    actual_json = actual_response.json()
    expected = {
        'application': 'pyconnect.main:app',
        'is_reload_enabled': False,
        'system_status': 'OK',
        'messaging_status': 'OK',
        'database_status': 'OK'
    }
    assert actual_json == expected
