"""
test_fhir.py
Tests the /fhir endpoint
"""
import asyncio
import pytest
from connect.clients import kafka, nats
from connect.config import get_settings
from connect.exceptions import FhirValidationError
from connect.routes.fhir import validate
from connect.workflows.core import CoreWorkflow
from fhir.resources.encounter import Encounter
from unittest.mock import AsyncMock


@pytest.fixture
def encounter_fixture():
    return {
        "resourceType": "Encounter",
        "id": "emerg",
        "text": {
            "status": "generated",
            "div": "\u003cdiv xmlns\u003d'http://www.w3.org/1999/xhtml'\u003eEmergency visit that escalated into inpatient patient @example\u003c/div\u003e",
        },
        "status": "in-progress",
        "statusHistory": [
            {
                "status": "arrived",
                "period": {
                    "start": "2017-02-01T07:15:00+10:00",
                    "end": "2017-02-01T07:35:00+10:00",
                },
            },
            {
                "status": "triaged",
                "period": {
                    "start": "2017-02-01T07:35:00+10:00",
                    "end": "2017-02-01T08:45:00+10:00",
                },
            },
            {
                "status": "in-progress",
                "period": {
                    "start": "2017-02-01T08:45:00+10:00",
                    "end": "2017-02-01T12:15:00+10:00",
                },
            },
            {
                "status": "onleave",
                "period": {
                    "start": "2017-02-01T12:15:00+10:00",
                    "end": "2017-02-01T12:45:00+10:00",
                },
            },
            {"status": "in-progress", "period": {"start": "2017-02-01T12:45:00+10:00"}},
        ],
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "IMP",
            "display": "inpatient encounter",
        },
        "classHistory": [
            {
                "class": {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                    "code": "EMER",
                    "display": "emergency",
                },
                "period": {
                    "start": "2017-02-01T07:15:00+10:00",
                    "end": "2017-02-01T09:27:00+10:00",
                },
            },
            {
                "class": {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                    "code": "IMP",
                    "display": "inpatient encounter",
                },
                "period": {"start": "2017-02-01T09:27:00+10:00"},
            },
        ],
        "subject": {"reference": "Patient/example"},
        "period": {"start": "2017-02-01T07:15:00+10:00"},
        "hospitalization": {
            "admitSource": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/admit-source",
                        "code": "emd",
                        "display": "From accident/emergency department",
                    }
                ]
            }
        },
        "location": [
            {
                "location": {"display": "Emergency Waiting Room"},
                "status": "active",
                "period": {
                    "start": "2017-02-01T07:15:00+10:00",
                    "end": "2017-02-01T08:45:00+10:00",
                },
            },
            {
                "location": {"display": "Emergency"},
                "status": "active",
                "period": {
                    "start": "2017-02-01T08:45:00+10:00",
                    "end": "2017-02-01T09:27:00+10:00",
                },
            },
            {
                "location": {"display": "Ward 1, Room 42, Bed 1"},
                "status": "active",
                "period": {
                    "start": "2017-02-01T09:27:00+10:00",
                    "end": "2017-02-01T12:15:00+10:00",
                },
            },
            {
                "location": {"display": "Ward 1, Room 42, Bed 1"},
                "status": "reserved",
                "period": {
                    "start": "2017-02-01T12:15:00+10:00",
                    "end": "2017-02-01T12:45:00+10:00",
                },
            },
            {
                "location": {"display": "Ward 1, Room 42, Bed 1"},
                "status": "active",
                "period": {"start": "2017-02-01T12:45:00+10:00"},
            },
        ],
        "meta": {
            "tag": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
                    "code": "HTEST",
                    "display": "test health data",
                }
            ]
        },
    }


@pytest.mark.asyncio
async def test_fhir_post(
    async_test_client,
    encounter_fixture,
    mock_async_kafka_producer,
    monkeypatch,
    settings,
):
    """
    Tests /fhir [POST] where data is not transmitted to an external server
    :param async_test_client: HTTPX test client fixture
    :param encounter_fixture: FHIR R4 Encounter Resource fixture
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

            actual_response = await ac.post("/fhir/Encounter", json=encounter_fixture)

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
    encounter_fixture,
    mock_async_kafka_producer,
    monkeypatch,
    settings,
):
    """
    Tests /fhir [POST] with an external FHIR server defined.
    :param async_test_client: HTTPX test client fixture
    :param encounter_fixture: FHIR R4 Encounter Resource fixture
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
            actual_response = await ac.post("/fhir/Encounter", json=encounter_fixture)
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
    encounter_fixture,
    mock_async_kafka_producer,
    monkeypatch,
    settings,
):
    """
    Tests /fhir [POST] endpoints to ensure that 404 and 422 status codes are returned when appropriate
    :param async_test_client: HTTPX test client fixture
    :param encounter_fixture: FHIR R4 Encounter Resource fixture
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

            actual_response = await ac.post("/fhir/Encounter", json=encounter_fixture)
            assert actual_response.status_code == 200

            actual_response = await ac.post("/fhir/encounter", json=encounter_fixture)
            assert actual_response.status_code == 404

            encounter_fixture["resourceType"] = "Patient"
            actual_response = await ac.post("/fhir/Encounter", json=encounter_fixture)
            assert actual_response.status_code == 422

            # a missing FHIR resource type also causes a 422
            del encounter_fixture["resourceType"]
            actual_response = await ac.post("/fhir/Encounter", json=encounter_fixture)
            assert actual_response.status_code == 422


def test_validate(encounter_fixture):
    """
    Tests the FHIR route validate() where the resource is valid
    """
    result = validate("Encounter", encounter_fixture)
    assert isinstance(result, Encounter)


def test_validate_invalid_resource_type(encounter_fixture):
    """
    Tests FhirWorkflow.validate where the resourceType in the message does not match the actual resource
    """
    encounter = encounter_fixture
    encounter["resourceType"] = "NoSuchResourceName"
    with pytest.raises(FhirValidationError):
        validate("Encounter", encounter)
