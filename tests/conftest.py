"""
conftest.py
Contains global/common pytest fixtures
"""
from pyconnect.config import Settings
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
