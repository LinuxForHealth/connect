import pytest
from connect.clients import kafka, nats
from connect.config import get_settings
from connect.workflows.core import CoreWorkflow
from unittest.mock import AsyncMock


@pytest.mark.parametrize(
    "fixture_name,data_format",
    [
        ("x12_fixture", "X12-005010"),
        ("fhir_fixture", "FHIR-R4"),
        ("hl7_fixture", "HL7-V2"),
    ],
)
@pytest.mark.asyncio
async def test_ingress_post(
    fixture_name,
    data_format,
    request,
    async_test_client,
    mock_async_kafka_producer,
    monkeypatch,
    settings,
):
    """
    Parameterized /ingress [POST] test with X12, FHIR, and HL7 inputs
    :param fixture_name: The name of the pytest fixture used for parameterized testing.
    :param data_format: The expected data format for the test case.
    :param request: The pytest request fixture used to dynamically access test case fixtures
    :param async_test_client: An async test client
    :param mock_async_kafka_producer: Mock async kafka producer used to simulate messaging interactions
    :param monkeypatch: The pytest monkeypatch fixture.
    :param settings: Mocked connect configuration settings.
    """
    fixture = request.getfixturevalue(fixture_name)
    with monkeypatch.context() as m:
        m.setattr(kafka, "ConfluentAsyncKafkaProducer", mock_async_kafka_producer)
        m.setattr(CoreWorkflow, "synchronize", AsyncMock())
        m.setattr(nats, "get_nats_client", AsyncMock(return_value=AsyncMock()))

        async with async_test_client as ac:
            # remove external server setting
            settings.connect_external_fhir_servers = []
            ac._transport.app.dependency_overrides[get_settings] = lambda: settings

            actual_response = await ac.post("/ingress", json={"data": fixture})

    assert actual_response.status_code == 200
    actual_json = actual_response.json()
    assert actual_json["uuid"]
    assert actual_json["operation"] == "POST"
    assert actual_json["creation_date"]
    assert actual_json["store_date"]
    assert actual_json["consuming_endpoint_url"] == "/ingress"
    assert actual_json["data"]
    assert actual_json["data_format"] == data_format
    assert actual_json["status"] == "success"
    assert data_format in actual_json["data_record_location"]
    assert actual_json["target_endpoint_urls"] == []
    assert actual_json["ipfs_uri"] is None
    assert actual_json["elapsed_storage_time"] > 0
    assert actual_json["elapsed_storage_time"] > 0
    assert actual_json["transmit_date"] is None
    assert actual_json["elapsed_transmit_time"] is None
    assert actual_json["elapsed_total_time"] > 0
    assert actual_json["transmission_attributes"] is None


@pytest.mark.asyncio
async def test_ingress_post_422_error(
    async_test_client, mock_async_kafka_producer, monkeypatch, settings, x12_fixture
):
    """
    Parameterized /ingress [POST] test with X12, FHIR, and HL7 inputs
    :param async_test_client: An async test client
    :param mock_async_kafka_producer: Mock async kafka producer used to simulate messaging interactions
    :param monkeypatch: The pytest monkeypatch fixture.
    :param settings: Mocked connect configuration settings.
    """
    invalid_x12 = x12_fixture.replace("ISA", "IPA")

    async with async_test_client as ac:
        # remove external server setting
        settings.connect_external_fhir_servers = []
        ac._transport.app.dependency_overrides[get_settings] = lambda: settings
        actual_response = await ac.post("/ingress", json={"data": invalid_x12})

    assert actual_response.status_code == 422


@pytest.mark.asyncio
async def test_edi_upload(
    dicom_fixture,
    tmpdir,
    async_test_client,
    mock_async_kafka_producer,
    monkeypatch,
    settings,
):
    with monkeypatch.context() as m:
        m.setattr(kafka, "ConfluentAsyncKafkaProducer", mock_async_kafka_producer)
        m.setattr(CoreWorkflow, "synchronize", AsyncMock())
        m.setattr(nats, "get_nats_client", AsyncMock(return_value=AsyncMock()))

        async with async_test_client as ac:
            # remove external server setting
            settings.connect_external_fhir_servers = []
            ac._transport.app.dependency_overrides[get_settings] = lambda: settings

            actual_response = await ac.post(
                "/ingress/upload", files={"file": ("dcm_1.dcm", dicom_fixture)}
            )

    assert actual_response.status_code == 200
    actual_json = actual_response.json()
    assert actual_json["uuid"]
    assert actual_json["operation"] == "POST"
    assert actual_json["creation_date"]
    assert actual_json["store_date"]
    assert actual_json["consuming_endpoint_url"] == "/ingress/upload"
    assert actual_json["data"]
    assert actual_json["data_format"] == "DICOM"
    assert actual_json["status"] == "success"
    assert "DICOM" in actual_json["data_record_location"]
    assert actual_json["target_endpoint_urls"] == []
    assert actual_json["ipfs_uri"] is None
    assert actual_json["elapsed_storage_time"] > 0
    assert actual_json["elapsed_storage_time"] > 0
    assert actual_json["transmit_date"] is None
    assert actual_json["elapsed_transmit_time"] is None
    assert actual_json["elapsed_total_time"] > 0
    assert actual_json["transmission_attributes"] is None
