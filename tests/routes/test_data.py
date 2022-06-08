"""
test_data.py
Tests /data endpoints
"""
import pytest

from connect.exceptions import KafkaMessageNotFoundError
from connect.routes import data
from unittest.mock import Mock


@pytest.fixture
def endpoint_parameters():
    return {"dataformat": "EXAMPLE", "partition": 100, "offset": 4561}


def test_get_data_ok(
    mock_async_kafka_consumer, session_test_client, endpoint_parameters, monkeypatch
):
    """
    Tests /data where a 200 status code is returned
    :param mock_async_kafka_consumer: The mock kafka consumer
    :param session_test_client: The configured Fast API test client, includes app and settings.
    :param endpoint_parameters: The endpoint parameters fixture
    :param monkeypatch: pyTest monkeypatch fixture
    """
    with monkeypatch.context() as m:
        m.setattr(
            data, "get_kafka_consumer", Mock(return_value=mock_async_kafka_consumer)
        )

        actual_response = session_test_client.get(
            "https://testserver/data", params=endpoint_parameters
        )

    assert actual_response.status_code == 200
    actual_json = actual_response.json()
    assert actual_json["data_record_location"] == "EXAMPLE:100:4561"


def test_get_data_bad_request(
    mock_async_kafka_consumer, session_test_client, endpoint_parameters, monkeypatch
):
    """
    Tests /data where a 400 status code is returned
    :param mock_async_kafka_consumer: The mock kafka consumer
    :param session_test_client: The configured Fast API test client, includes app and settings.
    :param endpoint_parameters: The endpoint parameters fixture
    :param monkeypatch: pyTest monkeypatch fixture
    """
    mock_async_kafka_consumer.get_message_from_kafka_cb.side_effect = ValueError(
        "Test bad request"
    )
    with monkeypatch.context() as m:
        m.setattr(
            data, "get_kafka_consumer", Mock(return_value=mock_async_kafka_consumer)
        )
        actual_response = session_test_client.get(
            "https://testserver/data", params=endpoint_parameters
        )

    assert actual_response.status_code == 400
    actual_json = actual_response.json()
    assert actual_json["detail"] == "Test bad request"


def test_get_data_not_found(
    mock_async_kafka_consumer, session_test_client, endpoint_parameters, monkeypatch
):
    """
    Tests /data where a 404 status code is returned
    :param mock_async_kafka_consumer: The mock kafka consumer
    :param session_test_client: The configured Fast API test client, includes app and settings.
    :param endpoint_parameters: The endpoint parameters fixture
    :param monkeypatch: pyTest monkeypatch fixture
    """
    mock_async_kafka_consumer.get_message_from_kafka_cb.side_effect = (
        KafkaMessageNotFoundError("Data record not found")
    )
    with monkeypatch.context() as m:
        m.setattr(
            data, "get_kafka_consumer", Mock(return_value=mock_async_kafka_consumer)
        )
        actual_response = session_test_client.get(
            "https://testserver/data", params=endpoint_parameters
        )

    assert actual_response.status_code == 404
    actual_json = actual_response.json()
    assert actual_json["detail"] == "Data record not found"
