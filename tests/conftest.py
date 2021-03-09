"""
conftest.py
Contains global/common pytest fixtures
"""
from confluent_kafka import Producer
from pyconnect.config import (Settings,
                              get_settings)
from fastapi.testclient import TestClient
from httpx import AsyncClient
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
def async_test_client(monkeypatch) -> AsyncClient:
    """
    Creates an HTTPX AsyncClient for async API testing
    :param monkeypatch: monkeypatch fixture
    :return: HTTPX async test client
    """
    monkeypatch.setenv('PYCONNECT_CERT', './mycert.pem')
    monkeypatch.setenv('PYCONNECT_CERT_KEY', './mycert.key')
    from pyconnect.main import app
    app.dependency_overrides[get_settings] = lambda: settings
    return AsyncClient(app=app, base_url='http://testserver')


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


@pytest.fixture
def mock_async_kafka_producer() -> Callable:
    """
    Defines a MockKafkaProducer class used to mock producer calls to Kafka.
    :return: MockKafkaProducer class
    """
    class MockKafkaProducer:
        def __init__(self, configs, loop=None):
            self._producer = Producer(configs)

        def _poll_loop(self): pass

        def close(self): pass

        async def produce_with_callback(self, topic, value, on_delivery):
            """is successful for any topic and value using any producer callback"""
            class CallbackMessage:
                """ Message to send to producer callback"""
                @staticmethod
                def topic():
                    return topic

                @staticmethod
                def partition():
                    return 0

                @staticmethod
                def offset():
                    return 0

            on_delivery(None, CallbackMessage())

    return MockKafkaProducer
