"""
test_fhir.py
Tests the /fhir endpoint
"""
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

        # actual_json = actual_response.json()
        # assert 'id' in actual_json
        # assert 'active' in actual_json
        # assert 'gender' in actual_json
        # assert 'resourceType' in actual_json

        # expected = {
        #    "id": "001",
        #    "active": True,
        #    "gender": "male",
        #    "resourceType": "Patient"
        #}
        #assert actual_json == expected
