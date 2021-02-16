"""
test_status.py
Tests the /status API endpoints
"""
from pyconnect.config import get_settings


def test_status_get(test_client, settings):
    """
    Tests /status [GET]
    :param test_client: Fast API test client
    :param settings: Settings test fixture
    """
    test_client.app.dependency_overrides[get_settings] = lambda: settings
    actual_response = test_client.get('/status')
    assert actual_response.status_code == 200

    actual_json = actual_response.json()
    assert 'application_version' in actual_json
    assert 'elapsed_time' in actual_json
    assert actual_json['elapsed_time'] > 0.0

    expected = {
        'application': 'pyconnect.main:app',
        'application_version': actual_json['application_version'],
        'is_reload_enabled': False,
        'system_status': 'OK',
        'messaging_status': 'OK',
        'database_status': 'OK',
        'elapsed_time': actual_json['elapsed_time']
    }
    assert actual_json == expected
