"""
test_fhir.py
Tests the /fhir endpoint
"""
import socket
from pyconnect.config import get_settings

def test_fhir_post(test_client, settings, mock_client_socket, monkeypatch):
    """
    Tests /status [GET]
    :param test_client: Fast API test client
    :param settings: Settings test fixture
    :param mock_client_socket: Mock Client Socket Fixture
    :param monkeypatch: MonkeyPatch instance used to mock test cases
    """
    test_client.app.dependency_overrides[get_settings] = lambda: settings

    with monkeypatch.context() as m:
        m.setattr(socket, 'socket', mock_client_socket)

        actual_response = test_client.post('/fhir',
                                           json={
                                               "resourceType": "Patient",
                                               "id": "001",
                                               "active": True,
                                               "gender": "male"
                                           })
        assert actual_response.status_code == 200

        actual_json = actual_response.json()
        assert 'id' in actual_json
        assert 'active' in actual_json
        assert 'gender' in actual_json
        assert 'resourceType' in actual_json

        expected = {
            "id": "001",
            "active": True,
            "gender": "male",
            "resourceType": "Patient"
        }
        assert actual_json == expected
