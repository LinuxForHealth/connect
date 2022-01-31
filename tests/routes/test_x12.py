"""
test_x12.py

Tests the /x12 endpoints
"""

import pytest
from connect.clients import kafka, nats
from connect.config import get_settings
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_x12_post(
    async_test_client,
    x12_fixture,
    mock_async_kafka_producer,
    monkeypatch,
    settings,
):
    """
    Tests /x12 [POST] where data is not transmitted to an external server
    :param async_test_client: HTTPX test client fixture
    :param x12_fixture: ASC X12 270 (Eligibility) Fixture
    :param mock_async_kafka_producer: Mock Kafka producer fixture
    :param monkeypatch: MonkeyPatch instance used to mock test cases
    :param settings: connect configuration settings fixture
    """
    with monkeypatch.context() as m:
        m.setattr(kafka, "ConfluentAsyncKafkaProducer", mock_async_kafka_producer)
        m.setattr(nats, "get_nats_client", AsyncMock(return_value=AsyncMock()))
        m.setattr(nats, "get_jetstream_context", AsyncMock(return_value=AsyncMock()))

        async with async_test_client as ac:
            # remove external server setting
            settings.connect_external_fhir_servers = None
            ac._transport.app.dependency_overrides[get_settings] = lambda: settings

            actual_response = await ac.post("/x12", json={"x12": x12_fixture})
            actual_json = actual_response.json()

            assert actual_response.status_code == 200
            assert len(actual_json) == 1

            json_resource = actual_json[0]
            assert json_resource["consuming_endpoint_url"] == "/x12"
            assert json_resource["data_format"] == "X12-5010"
            assert json_resource["status"] == "success"
            assert json_resource["data_record_location"] == "X12-5010:0:0"

            # invalid request
            error_fixture: str = x12_fixture.replace("HL*1**20*1~", "HL*1**20~")
            actual_response = await ac.post("/x12", json={"x12": error_fixture})
            assert actual_response.status_code == 422
