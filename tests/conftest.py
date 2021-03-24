"""
conftest.py
Contains global/common pytest fixtures
"""
from confluent_kafka import Producer

from pyconnect.clients import ConfluentAsyncKafkaConsumer
from pyconnect.config import Settings
from fastapi.testclient import TestClient
from httpx import AsyncClient
from typing import Callable
import pytest
from unittest.mock import AsyncMock


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
        'pyconnect_cert': './mycert.pem',
        'fhir_r4_externalserver': 'https://fhiruser:change-password@localhost:9443/fhir-server/api/v4'
    }
    return Settings(**settings_fields)


@pytest.fixture
def lfh_data_record():
    """ A LFH Data Record Fixture"""
    return {
        'uuid': 'dbe0e8dd-7b64-4d7b-aefc-d27e2664b94a',
        'creation_date': '2021-02-12T18:13:17Z',
        'store_date': '2021-02-12T18:14:17Z',
        'transmit_date': '2021-02-12T18:15:17Z',
        'consuming_endpoint_url': 'https://localhost:8080/endpoint',
        'data_format': 'EXAMPLE',
        'data': 'SGVsbG8gV29ybGQhIEl0J3MgbWUu',
        'status': 'success',
        'data_record_location': 'EXAMPLE:100:4561',
        'target_endpoint_url': 'http://externalhost/endpoint',
        'elapsed_storage_time': 0.080413915000008,
        'elapsed_transmit_time': 0.080413915000008,
        'elapsed_total_time': 0.080413915000008
    }


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
    return AsyncClient(app=app, base_url='http://testserver')


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


@pytest.fixture
def mock_async_kafka_consumer(lfh_data_record):
    """
    A mock Kafka Consumer configured to return a LFH Data Record
    """
    mock = AsyncMock(spec=ConfluentAsyncKafkaConsumer)
    mock.get_message_from_kafka_cb = AsyncMock(return_value=lfh_data_record)
    return mock
