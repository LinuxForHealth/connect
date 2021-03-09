"""
test_fhir.py
Tests the /fhir endpoint
"""
import json
import pytest
from pyconnect import clients


@pytest.mark.asyncio
async def test_fhir_post(async_test_client, mock_async_kafka_producer, monkeypatch):
    """
    Tests /fhir [POST]
    :param async_test_client: HTTPX test client fixture
    :param mock_async_kafka_producer: Mock Kafka producer fixture
    :param monkeypatch: MonkeyPatch instance used to mock test cases
    """
    with monkeypatch.context() as m:
        m.setattr(clients, 'ConfluentAsyncKafkaProducer', mock_async_kafka_producer)

        async with async_test_client as ac:
            actual_response = await ac.post('/fhir',
                                            json={
                                                "resourceType": "Patient",
                                                "id": "001",
                                                "active": True,
                                                "gender": "male"
                                            })

        print(f'actual_response = {actual_response}')
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
        expected_data_str = json.dumps(expected_data)
        assert actual_json['data'] == expected_data_str
        assert actual_json['consuming_endpoint_url'] == '/fhir'
        assert actual_json['data_format'] == 'PATIENT'
        assert actual_json['status'] == 'success'
        assert actual_json['data_record_location'] == 'PATIENT:0:0'
