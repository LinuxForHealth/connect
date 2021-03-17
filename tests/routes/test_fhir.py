"""
test_fhir.py
Tests the /fhir endpoint
"""
import pytest
from pyconnect import clients
from pyconnect.support.encoding import (encode_from_dict,
                                        decode_to_dict)
from pyconnect.config import get_settings
from pyconnect.workflows.fhir import FhirWorkflow
from starlette.responses import Response
import asyncio


@pytest.mark.asyncio
async def test_fhir_post(async_test_client, mock_async_kafka_producer, monkeypatch, settings):
    """
    Tests /fhir [POST] where data is not transmitted to an external server
    :param async_test_client: HTTPX test client fixture
    :param mock_async_kafka_producer: Mock Kafka producer fixture
    :param monkeypatch: MonkeyPatch instance used to mock test cases
    :param settings: pyConnect configuration settings fixture
    """
    with monkeypatch.context() as m:
        m.setattr(clients, 'ConfluentAsyncKafkaProducer', mock_async_kafka_producer)

        async with async_test_client as ac:
            # remove external server setting
            settings.fhir_r4_externalserver = None
            ac._transport.app.dependency_overrides[get_settings] = lambda: settings

            actual_response = await ac.post('/fhir',
                                            json={
                                                "resourceType": "Patient",
                                                "id": "001",
                                                "active": True,
                                                "gender": "male"
                                            })

        assert actual_response.status_code == 200

        actual_json = actual_response.json()
        assert 'uuid' in actual_json
        assert 'creation_date' in actual_json
        assert 'store_date' in actual_json
        assert 'transmit_date' in actual_json
        assert 'target_endpoint_url' in actual_json
        assert 'elapsed_storage_time' in actual_json
        assert 'elapsed_transmit_time' in actual_json
        assert 'elapsed_total_time' in actual_json

        expected_data = {
            "id": "001",
            "active": True,
            "gender": "male",
            "resourceType": "Patient"
        }

        # encode the expected data and match
        expected_data_encoded = encode_from_dict(expected_data)
        assert actual_json['data'] == expected_data_encoded

        # decode the actual data and match
        actual_data = decode_to_dict(actual_json['data'])
        assert actual_data == expected_data

        assert actual_json['consuming_endpoint_url'] == '/fhir'
        assert actual_json['data_format'] == 'PATIENT'
        assert actual_json['status'] == 'success'
        assert actual_json['data_record_location'] == 'PATIENT:0:0'


@pytest.mark.asyncio
async def test_fhir_post_with_transmit(async_test_client, mock_async_kafka_producer, monkeypatch, settings):
    """
    Tests /fhir [POST] with an external FHIR server defined.
    :param async_test_client: HTTPX test client fixture
    :param mock_async_kafka_producer: Mock Kafka producer fixture
    :param monkeypatch: MonkeyPatch instance used to mock test cases
    :param settings: pyConnect configuration settings
    """
    async def mock_workflow_transmit(self, response: Response):
        """
        A mock workflow transmission method used to set a response returned to a client
        """
        await asyncio.sleep(.1)
        response.status_code = 201
        response.headers['location'] = 'fhir/v4/Patient/5d7dc79a-faf2-453d-9425-a0efe85032ea/_history/1'
        self.use_response = True

    with monkeypatch.context() as m:
        m.setattr(clients, 'ConfluentAsyncKafkaProducer', mock_async_kafka_producer)
        m.setattr(FhirWorkflow, 'transmit', mock_workflow_transmit)

        async with async_test_client as ac:
            ac._transport.app.dependency_overrides[get_settings] = lambda: settings
            actual_response = await ac.post('/fhir',
                                            json={
                                                "resourceType": "Patient",
                                                "id": "001",
                                                "active": True,
                                                "gender": "male"
                                            })

            assert actual_response.status_code == 201
            assert actual_response.text == ''
            assert 'location' in actual_response.headers
