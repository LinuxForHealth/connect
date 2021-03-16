"""
test_fhir.py
Tests the /fhir endpoint
"""
import pytest
from pyconnect.workflows import core
from unittest.mock import (Mock,
                           sentinel)
from asynctest import CoroutineMock
from pyconnect.support.encoding import (encode_from_dict,
                                        decode_to_dict)


_SAMPLE_LFH_DATA_RESPONSE = {
    'uuid': 'dbe0e8dd-7b64-4d7b-aefc-d27e2664b94a',
    'creation_date': '2021-02-12T18:13:17Z',
    'store_date': '2021-02-12T18:14:17Z',
    'transmit_date': '2021-02-12T18:15:17Z',
    'consuming_endpoint_url': '/fhir',
    'data_format': 'PATIENT',
    'data': {
             "id": "001",
             "active": True,
             "gender": "male",
             "resourceType": "Patient"
            },
    'status': 'success',
    'data_record_location': 'PATIENT:0:0',
    'target_endpoint_url': 'http://externalhost/endpoint',
    'elapsed_storage_time': 0.080413915000008,
    'elapsed_transmit_time': 0.080413915000008,
    'elapsed_total_time': 0.080413915000008

}


@pytest.mark.asyncio
async def test_fhir_post(async_test_client):
    """
    Tests /fhir [POST]
    :param async_test_client: HTTPX test client fixture
    # :param mock_async_kafka_producer: Mock Kafka producer fixture
    # :param monkeypatch: MonkeyPatch instance used to mock test cases
    """

    core.get_kafka_producer = Mock(name='get_kafka_producer')
    core.get_kafka_producer.return_value = sentinel.kafka_producer
    sentinel.kafka_producer.produce_with_callback = CoroutineMock()
    core.LinuxForHealthDataRecordResponse = Mock(return_value=_SAMPLE_LFH_DATA_RESPONSE)

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

    # encode the expected data and match
    expected_data_encoded = encode_from_dict(expected_data)
    actual_json_data_encoded = encode_from_dict(actual_json['data'])
    assert actual_json_data_encoded == expected_data_encoded

    # decode the actual data and match
    actual_data = decode_to_dict(actual_json_data_encoded)
    assert actual_data == expected_data

    assert actual_json['consuming_endpoint_url'] == '/fhir'
    assert actual_json['data_format'] == 'PATIENT'
    assert actual_json['status'] == 'success'
    assert actual_json['data_record_location'] == 'PATIENT:0:0'
