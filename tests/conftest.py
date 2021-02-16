"""
conftest.py
Contains global/common pytest fixtures
"""
from pyconnect.config import Settings
from fastapi.testclient import TestClient
import pytest


@pytest.fixture
def settings() -> Settings:
    """
    :return: Application Settings
    """
    settings_fields = {
        'uvicorn_reload': False,
        'uvicorn_app': 'pyconnect.main:app',
        'uvicorn_cert_key': './mycert.key',
        'uvicorn_cert': './mycert.pem'
    }
    return Settings(**settings_fields)


@pytest.fixture
def test_client(monkeypatch) -> TestClient:
    """
    Creates a Fast API Test Client for API testing
    :param monkeypatch: monkeypatch fixture
    :return: Fast API test client
    """
    monkeypatch.setenv('UVICORN_CERT', './mycert.pem')
    monkeypatch.setenv('UVICORN_CERT_KEY', './mycert.key')
    from pyconnect.main import app
    return TestClient(app)
