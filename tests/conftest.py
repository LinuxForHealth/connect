"""
conftest.py
Contains global/common pytest fixtures
"""
from pyconnect.config import Settings
from fastapi.testclient import TestClient
from typing import Callable
import pytest


@pytest.fixture
def settings() -> Settings:
    """
    :return: Application Settings
    """
    settings_fields = {
        'kafka_bootstrap_servers': ['localhost:8080'],
        'nats_servers': ['tls://localhost:8080'],
        'uvicorn_reload': False,
        'uvicorn_app': 'pyconnect.main:app',
        'pyconnect_cert_key': './mycert.key',
        'pyconnect_cert': './mycert.pem'
    }
    return Settings(**settings_fields)


@pytest.fixture
def test_client(monkeypatch) -> TestClient:
    """
    Creates a Fast API Test Client for API testing
    :param monkeypatch: monkeypatch fixture
    :return: Fast API test client
    """
    monkeypatch.setenv('PYCONNECT_CERT', './mycert.pem')
    monkeypatch.setenv('PYCONNECT_CERT_KEY', './mycert.key')
    from pyconnect.main import app
    return TestClient(app)


@pytest.fixture
def mock_client_socket() -> Callable:
    """
    Defines a MockClientSocket class used to mock client socket connections.
    The MockClientSocket class returns a positive result for addresses using port 8080.
    :return: MockClientSocket class
    """
    class MockClientSocket:

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def __init__(self, family: int, type: int):
            self.family = family
            self.type = type

        def connect(self, address: tuple):
            """Is successful for any host on port 8080"""
            if address is None or len(address) < 2 or address[1] != 8080:
                raise ConnectionError

    return MockClientSocket
