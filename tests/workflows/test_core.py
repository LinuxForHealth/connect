"""
test_core.py

Tests the processes and transitions defined within the Core Workflow implementation.
"""
import pytest
from pyconnect.workflows import core
from pyconnect.workflows.core import CoreWorkflow
import datetime
from unittest.mock import (AsyncMock,
                           Mock)


@pytest.fixture
def kafka_callback():
    class MockCallback:
        def __init__(self):
            self.kafka_result = 'CUSTOM:0:0'
            self.kafka_status = 'success'

        def get_kafka_result(self, err: object, msg: object):
            pass

    return MockCallback


@pytest.fixture
def workflow() -> CoreWorkflow:
    config = {
        'message': {'first_name': 'John', 'last_name': 'Doe'},
        'origin_url': 'http://localhost:5000/data',
        'certificate_verify': False,
        'lfh_id': '90cf887d-eaa0-4997-b2b7-b1e39ae0ec03',
        'data_format': 'custom'
    }
    workflow = CoreWorkflow(**config)
    workflow.transmit_server = 'https://external-server.com/data'
    return workflow


def test_init(workflow: CoreWorkflow):
    """
    Tests CoreWorkflow.__init__ and the state transition.
    :param workflow: The CoreWorkflow fixture
    """
    assert workflow.message == {'first_name': 'John', 'last_name': 'Doe'}
    assert workflow.data_format == 'custom'
    assert workflow.origin_url == 'http://localhost:5000/data'
    assert workflow.start_time is None
    assert workflow.use_response is False
    assert workflow.verify_certs is False
    assert workflow.lfh_exception_topic == 'LFH_EXCEPTION'
    assert workflow.lfh_id == '90cf887d-eaa0-4997-b2b7-b1e39ae0ec03'

    assert workflow.state == 'parse'


@pytest.mark.asyncio
async def test_manual_flow_with_transmit(workflow: CoreWorkflow,
                                         monkeypatch,
                                         kafka_callback,
                                         mock_httpx_client):
    """
    Manually tests CoreWorkflow state transitions where data is transmitted
    """
    workflow.start_time = datetime.datetime.utcnow()
    nats_mock = AsyncMock()

    with monkeypatch.context() as m:
        m.setattr(core, 'get_kafka_producer', Mock(return_value=AsyncMock()))
        m.setattr(core, 'KafkaCallback', kafka_callback)
        m.setattr(core, 'AsyncClient', mock_httpx_client)
        m.setattr(core, 'get_nats_client', AsyncMock(return_value=nats_mock))

        workflow.validate()
        assert workflow.state.name == 'validate'

        workflow.transform()
        assert workflow.state.name == 'transform'

        await workflow.persist()
        assert workflow.state.name == 'persist'
        assert workflow.message['elapsed_storage_time'] > 0
        assert workflow.message['elapsed_total_time'] > 0
        assert workflow.message['data_record_location'] == 'CUSTOM:0:0'
        assert workflow.message['status'] == 'success'

        await workflow.transmit(Mock())
        assert workflow.state.name == 'transmit'
        assert workflow.message['transmit_date'] is not None
        assert workflow.message['elapsed_transmit_time'] > 0
        assert workflow.use_response is True

        await workflow.synchronize()
        assert workflow.state.name == 'sync'
        nats_mock.publish.assert_called_once()
