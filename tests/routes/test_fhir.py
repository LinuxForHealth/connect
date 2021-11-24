"""
test_fhir.py
Tests the /fhir endpoint
"""
import asyncio
import pytest
import json
from typing import Dict
from connect.clients import kafka, nats
from connect.config import get_settings
from connect.exceptions import FhirValidationError
from connect.routes.fhir import validate
from connect.workflows.core import CoreWorkflow
from fhir.resources.encounter import Encounter
from unittest.mock import AsyncMock


@pytest.fixture
def fhir_resource(fhir_fixture) -> Dict:
    return json.loads(fhir_fixture)


@pytest.mark.asyncio
async def test_fhir_post(
    async_test_client,
    fhir_resource,
    mock_async_kafka_producer,
    monkeypatch,
    settings,
):
    """
    Tests /fhir [POST] where data is not transmitted to an external server
    :param async_test_client: HTTPX test client fixture
    :param fhir_resource: FHIR R4 Encounter Resource fixture
    :param mock_async_kafka_producer: Mock Kafka producer fixture
    :param monkeypatch: MonkeyPatch instance used to mock test cases
    :param settings: connect configuration settings fixture
    """
    with monkeypatch.context() as m:
        m.setattr(kafka, "ConfluentAsyncKafkaProducer", mock_async_kafka_producer)
        m.setattr(CoreWorkflow, "synchronize", AsyncMock())
        m.setattr(nats, "get_nats_client", AsyncMock(return_value=AsyncMock()))

        async with async_test_client as ac:
            # remove external server setting
            settings.connect_external_fhir_servers = []
            ac._transport.app.dependency_overrides[get_settings] = lambda: settings
            actual_response = await ac.post("/fhir/Encounter", json=fhir_resource)

        assert actual_response.status_code == 200

        actual_json = actual_response.json()
        assert "uuid" in actual_json
        assert "creation_date" in actual_json
        assert "store_date" in actual_json
        assert "transmit_date" in actual_json
        assert "target_endpoint_urls" in actual_json
        assert "elapsed_storage_time" in actual_json
        assert "elapsed_transmit_time" in actual_json
        assert "elapsed_total_time" in actual_json

        assert actual_json["consuming_endpoint_url"] == "/fhir/Encounter"
        assert actual_json["data_format"] == "FHIR-R4"
        assert actual_json["status"] == "success"
        assert actual_json["data_record_location"] == "FHIR-R4:0:0"


@pytest.mark.asyncio
async def test_fhir_post_with_transmit(
    async_test_client,
    fhir_resource,
    mock_async_kafka_producer,
    monkeypatch,
    settings,
):
    """
    Tests /fhir [POST] with an external FHIR server defined.
    :param async_test_client: HTTPX test client fixture
    :param fhir_resource: FHIR R4 Encounter Resource fixture
    :param mock_async_kafka_producer: Mock Kafka producer fixture
    :param monkeypatch: MonkeyPatch instance used to mock test cases
    :param settings: connect configuration settings
    """

    async def mock_workflow_transmit(self):
        """
        A mock workflow transmission method used to set a response returned to a client
        """
        await asyncio.sleep(0.1)
        result = [
            {
                "url": "https://fhiruser:change-password@localhost:9443/fhir-server/api/v4/Patient",
                "result": "",
                "status_code": 201,
                "headers": {
                    "location": "https://127.0.0.1:5000/fhir-server/api/v4/Patient/17c5ff8e0fa-b8562320-7070-4a83-9312-91938bb97c9e/_history/1",
                    "etag": 'W/"1"',
                    "last-modified": "Fri, 08 Oct 2021 12:55:18 GMT",
                    "date": "Fri, 08 Oct 2021 12:55:18 GMT",
                    "content-length": "0",
                    "content-language": "en-US",
                },
            }
        ]
        return result

    with monkeypatch.context() as m:
        m.setattr(kafka, "ConfluentAsyncKafkaProducer", mock_async_kafka_producer)
        m.setattr(CoreWorkflow, "transmit", mock_workflow_transmit)
        m.setattr(CoreWorkflow, "synchronize", AsyncMock())
        m.setattr(nats, "get_nats_client", AsyncMock(return_value=AsyncMock()))

        async with async_test_client as ac:
            ac._transport.app.dependency_overrides[get_settings] = lambda: settings
            actual_response = await ac.post("/fhir/Encounter", json=fhir_resource)
            actual_json = actual_response.json()

            assert (
                actual_json[0]["url"]
                == "https://fhiruser:change-password@localhost:9443/fhir-server/api/v4/Patient"
            )
            assert actual_json[0]["result"] == ""
            assert actual_json[0]["status_code"] == 201
            assert "location" in actual_json[0]["headers"]


@pytest.mark.asyncio
async def test_fhir_post_endpoints(
    async_test_client,
    fhir_resource,
    mock_async_kafka_producer,
    monkeypatch,
    settings,
):
    """
    Tests /fhir [POST] endpoints to ensure that 404 and 422 status codes are returned when appropriate
    :param async_test_client: HTTPX test client fixture
    :param fhir_resource: FHIR R4 Encounter Resource fixture
    :param mock_async_kafka_producer: Mock Kafka producer fixture
    :param monkeypatch: MonkeyPatch instance used to mock test cases
    :param settings: connect configuration settings fixture
    """
    with monkeypatch.context() as m:
        m.setattr(kafka, "ConfluentAsyncKafkaProducer", mock_async_kafka_producer)
        m.setattr(CoreWorkflow, "synchronize", AsyncMock())
        m.setattr(nats, "get_nats_client", AsyncMock(return_value=AsyncMock()))

        async with async_test_client as ac:
            # remove external server setting
            settings.connect_external_fhir_servers = []
            ac._transport.app.dependency_overrides[get_settings] = lambda: settings

            actual_response = await ac.post("/fhir/Encounter", json=fhir_resource)
            assert actual_response.status_code == 200

            actual_response = await ac.post("/fhir/encounter", json=fhir_resource)
            assert actual_response.status_code == 404

            fhir_resource["resourceType"] = "Patient"
            actual_response = await ac.post("/fhir/Encounter", json=fhir_resource)
            assert actual_response.status_code == 422

            # a missing FHIR resource type also causes a 422
            del fhir_resource["resourceType"]
            actual_response = await ac.post("/fhir/Encounter", json=fhir_resource)
            assert actual_response.status_code == 422


def test_validate(fhir_resource):
    """
    Tests the FHIR route validate() where the resource is valid
    """
    result = validate("Encounter", fhir_resource)
    assert isinstance(result, Encounter)


def test_validate_invalid_resource_type(fhir_resource):
    """
    Tests FhirWorkflow.validate where the resourceType in the message does not match the actual resource
    """
    fhir_resource["resourceType"] = "NoSuchResourceName"
    with pytest.raises(FhirValidationError):
        validate("Encounter", fhir_resource)
