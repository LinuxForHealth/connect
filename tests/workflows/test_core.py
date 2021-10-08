"""
test_core.py

Tests the processes and transitions defined within the Core Workflow implementation.
"""
from fastapi import Response
import connect.clients.nats as nats
import pytest
from connect.workflows import core
from connect.workflows.core import CoreWorkflow
import datetime
from unittest.mock import AsyncMock, Mock


@pytest.fixture
def kafka_callback():
    class MockCallback:
        def __init__(self):
            self.kafka_result = "CUSTOM:0:0"
            self.kafka_status = "success"

        def get_kafka_result(self, err: object, msg: object):
            pass

    return MockCallback


@pytest.fixture
def workflow() -> CoreWorkflow:
    config = {
        "message": {"first_name": "John", "last_name": "Doe"},
        "origin_url": "http://localhost:5000/data",
        "certificate_verify": False,
        "lfh_id": "90cf887d-eaa0-4997-b2b7-b1e39ae0ec03",
        "data_format": "custom",
        "operation": "POST",
    }
    workflow = CoreWorkflow(**config)
    return workflow


def test_init(workflow: CoreWorkflow):
    """
    Tests CoreWorkflow.__init__.
    :param workflow: The CoreWorkflow fixture
    """
    assert workflow.message == {"first_name": "John", "last_name": "Doe"}
    assert workflow.data_format == "custom"
    assert workflow.origin_url == "http://localhost:5000/data"
    assert workflow.start_time is None
    assert workflow.verify_certs is False
    assert workflow.lfh_exception_topic == "LFH_EXCEPTION"
    assert workflow.lfh_id == "90cf887d-eaa0-4997-b2b7-b1e39ae0ec03"


@pytest.mark.asyncio
async def test_manual_flow(
    workflow: CoreWorkflow, monkeypatch, kafka_callback, mock_httpx_client
):
    """
    Manually tests CoreWorkflow.  The testing order mirrors the execution order provider in
    CoreWorkflow.run.

    :param workflow: The CoreWorkflow fixture
    :param monkeypatch: Pytest monkeypatch fixture
    :param kafka_callback: KafkaCallback fixture
    :param mock_httpx_client: Mock HTTPX Client fixture
    """
    workflow.start_time = datetime.datetime.utcnow()
    nats_mock = AsyncMock()

    with monkeypatch.context() as m:
        m.setattr(core, "get_kafka_producer", Mock(return_value=AsyncMock()))
        m.setattr(core, "KafkaCallback", kafka_callback)
        m.setattr(core, "AsyncClient", mock_httpx_client)
        m.setattr(nats, "get_nats_client", AsyncMock(return_value=nats_mock))

        await workflow.transform()

        await workflow.persist()
        assert workflow.message["elapsed_storage_time"] > 0
        assert workflow.message["elapsed_total_time"] > 0
        assert workflow.message["data_record_location"] == "CUSTOM:0:0"
        assert workflow.message["status"] == "success"

        workflow.transmit_servers = ["https://external-server.com/data"]
        workflow.transmission_attributes["tenant_id"] = "MyTenant"
        await workflow.transmit()
        assert workflow.message["transmit_date"] is not None
        assert workflow.message["elapsed_transmit_time"] > 0
        assert len(workflow.transmission_attributes) == 2
        assert workflow.transmission_attributes["tenant_id"] == "MyTenant"
        assert "content-length" in workflow.transmission_attributes
        await workflow.synchronize()
        assert nats_mock.publish.call_count == 5


@pytest.mark.asyncio
async def test_run_flow(
    workflow: CoreWorkflow, monkeypatch, kafka_callback, mock_httpx_client
):
    """
    Tests the CoreWorkflow.run method.

    :param workflow: The CoreWorkflow fixture
    :param monkeypatch: Pytest monkeypatch fixture
    :param kafka_callback: KafkaCallback fixture
    :param mock_httpx_client: Mock HTTPX Client fixture
    """
    workflow.start_time = datetime.datetime.utcnow()

    with monkeypatch.context() as m:
        m.setattr(core, "get_kafka_producer", Mock(return_value=AsyncMock()))
        m.setattr(core, "KafkaCallback", kafka_callback)
        m.setattr(core, "AsyncClient", mock_httpx_client)
        m.setattr(nats, "get_nats_client", AsyncMock(return_value=AsyncMock()))

        result = await workflow.run()
        actual_value = workflow.set_response(Response(), result)
        assert actual_value["consuming_endpoint_url"] == "http://localhost:5000/data"
        assert actual_value["creation_date"] is not None
        assert (
            actual_value["data"]
            == "eyJmaXJzdF9uYW1lIjogIkpvaG4iLCAibGFzdF9uYW1lIjogIkRvZSJ9"
        )
        assert actual_value["data_format"] == "custom"
        assert actual_value["data_record_location"] == "CUSTOM:0:0"
        assert actual_value["elapsed_storage_time"] > 0
        assert actual_value["elapsed_total_time"] > 0
        assert actual_value["elapsed_transmit_time"] is None
        assert actual_value["lfh_id"] is not None
        assert actual_value["status"] == "success"
        assert actual_value["store_date"] is not None
        assert actual_value["target_endpoint_urls"] == []
        assert actual_value["transmit_date"] is None
        assert actual_value["uuid"] is not None


@pytest.mark.asyncio
async def test_run_flow_error(
    workflow: CoreWorkflow, monkeypatch, kafka_callback, mock_httpx_client
):
    """
    Tests the CoreWorkflow.run method when an exception occurs

    :param workflow: The CoreWorkflow fixture
    :param monkeypatch: Pytest monkeypatch fixture
    :param kafka_callback: KafkaCallback fixture
    :param mock_httpx_client: Mock HTTPX Client fixture
    """
    workflow.start_time = datetime.datetime.utcnow()
    workflow.persist = Mock(side_effect=Exception("test exception"))

    with monkeypatch.context() as m:
        m.setattr(core, "get_kafka_producer", Mock(return_value=AsyncMock()))
        m.setattr(core, "KafkaCallback", kafka_callback)
        m.setattr(core, "AsyncClient", mock_httpx_client)
        m.setattr(nats, "get_nats_client", AsyncMock(return_value=AsyncMock()))

        with pytest.raises(Exception):
            await workflow.run()
