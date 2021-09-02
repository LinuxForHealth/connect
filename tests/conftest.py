"""
conftest.py
Contains global/common pytest fixtures
"""

from confluent_kafka import Producer
from connect.clients.kafka import ConfluentAsyncKafkaConsumer
from connect.config import Settings
from fastapi.testclient import TestClient
from httpx import AsyncClient, Response
from typing import Callable
import pytest
from unittest.mock import AsyncMock
from connect.main import get_app
from nats.aio.client import Client as NatsClient


@pytest.fixture
def settings() -> Settings:
    """
    :return: Application Settings
    """
    settings_fields = {
        "kafka_bootstrap_servers": ["localhost:8080"],
        "nats_servers": ["tls://localhost:8080"],
        "uvicorn_reload": False,
        "uvicorn_app": "connect.asgi:app",
        "connect_cert_key_name": "./mycert.key",
        "connect_cert_name": "./mycert.pem",
        "connect_external_fhir_servers": [
            "https://fhiruser:change-password@localhost:9443/fhir-server/api/v4"
        ],
    }
    return Settings(**settings_fields)


@pytest.fixture
def lfh_data_record():
    """
    :return: LFH Data Record Fixture
    """
    return {
        "uuid": "dbe0e8dd-7b64-4d7b-aefc-d27e2664b94a",
        "creation_date": "2021-02-12T18:13:17Z",
        "store_date": "2021-02-12T18:14:17Z",
        "transmit_date": "2021-02-12T18:15:17Z",
        "consuming_endpoint_url": "https://localhost:8080/endpoint",
        "data_format": "EXAMPLE",
        "data": "SGVsbG8gV29ybGQhIEl0J3MgbWUu",
        "status": "success",
        "data_record_location": "EXAMPLE:100:4561",
        "target_endpoint_urls": ["http://externalhost/endpoint"],
        "elapsed_storage_time": 0.080413915000008,
        "elapsed_transmit_time": 0.080413915000008,
        "elapsed_total_time": 0.080413915000008,
    }


@pytest.fixture
def test_client(monkeypatch) -> TestClient:
    """
    Creates a Fast API Test Client for API testing
    :param monkeypatch: monkeypatch fixture
    :return: Fast API test client
    """
    monkeypatch.setenv("CONNECT_CERT", "./mycert.pem")
    monkeypatch.setenv("CONNECT_CERT_KEY", "./mycert.key")
    return TestClient(get_app())


@pytest.fixture
def async_test_client(monkeypatch) -> AsyncClient:
    """
    Creates an HTTPX AsyncClient for async API testing
    :param monkeypatch: monkeypatch fixture
    :return: HTTPX async test client
    """
    monkeypatch.setenv("CONNECT_CERT", "./mycert.pem")
    monkeypatch.setenv("CONNECT_CERT_KEY", "./mycert.key")

    return AsyncClient(app=get_app(), base_url="http://testserver")


@pytest.fixture
def mock_async_kafka_producer() -> Callable:
    """
    Defines a MockKafkaProducer class used to mock producer calls to Kafka.
    :return: MockKafkaProducer class
    """

    class MockKafkaProducer:
        def __init__(self, configs, loop=None):
            self._producer = Producer(configs)

        def _poll_loop(self):
            pass

        def close(self):
            pass

        async def produce_with_callback(self, topic, value, on_delivery):
            """
            Implements a producer with a callback
            """

            class CallbackMessage:
                """
                Message to send to producer callback
                """

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


@pytest.fixture
def mock_httpx_client():
    """
    Returns a mock HTTPX Client instance which supports use as a context manager
    """

    class MockHttpxClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        def _return_mock_response(self):
            """
            Returns an AsyncMock "response" object supporting:
            - status_code
            - text
            - headers
            """
            mock_response = AsyncMock(spec=Response)
            mock_response.status_code = 200
            mock_response.text = "response-text"
            mock_response.headers = {}
            return mock_response

        async def post(self, *args, **kwargs):
            return self._return_mock_response()

        async def get(self, *args, **kwargs):
            return self._return_mock_response()

    return MockHttpxClient


@pytest.fixture
def nats_client() -> AsyncMock:
    """Returns an AsyncMock Nats Client"""
    mock = AsyncMock(spec=NatsClient)
    return mock
