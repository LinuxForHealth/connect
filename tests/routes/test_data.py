"""
test_data.py
Tests /data endpoints
"""
import pytest
from confluent_kafka import KafkaException
from pyconnect.routes import data
from unittest.mock import (Mock,
                           sentinel)
from asynctest import CoroutineMock
from pyconnect.exceptions import KafkaMessageNotFoundError

_EXAMPLE_DATA_RECORD = {
    'uuid': 'dbe0e8dd-7b64-4d7b-aefc-d27e2664b94a',
    'creation_date': '2021-02-12T18:13:17Z',
    'store_date': '2021-02-12T18:14:17Z',
    'transmit_date': '2021-02-12T18:15:17Z',
    'consuming_endpoint_url': 'https://localhost:8080/endpoint',
    'data_format': 'EXAMPLE',
    'data': 'SGVsbG8gV29ybGQhIEl0J3MgbWUu',
    'status': 'success',
    'data_record_location': 'EXAMPLE:100:4561',
    'target_endpoint_url': 'http://externalhost/endpoint',
    'elapsed_storage_time': 0.080413915000008,
    'elapsed_transmit_time': 0.080413915000008,
    'elapsed_total_time': 0.080413915000008
}


@pytest.mark.asyncio
async def test_get_data_record(async_test_client):
    """
    Tests /data?dataFormat=x&partition=0&offset=0
    :param test_client: Fast API test client
    """

    # Happy path with a 200 response from Mocked KafkaConsumer
    data.get_kafka_consumer = Mock(name='get_kafka_consumer')
    data.get_kafka_consumer.return_value = sentinel.kafka_consumer
    sentinel.kafka_consumer.get_message_from_kafka_cb = CoroutineMock(return_value=_EXAMPLE_DATA_RECORD)

    async with async_test_client as atc:
        actual_response = await atc.get('/data',
                                        params={
                                           'dataformat': 'EXAMPLE',
                                           'partition': 100,
                                           'offset': 4561
                                        })

    assert actual_response.status_code == 200
    actual_json = actual_response.json()
    assert actual_json['data_record_location'] == 'EXAMPLE:100:4561'

    #
    # Mock raising a ValueError and assert handling with a 400 BAD REQUEST response
    sentinel.kafka_consumer.get_message_from_kafka_cb = CoroutineMock(side_effect=ValueError('Test bad response'))
    async with async_test_client as atc:
        actual_response = await atc.get('/data',
                                        params={
                                           'dataformat': 'some_topic',
                                           'partition': 0,
                                           'offset': 123
                                        })

    assert actual_response.status_code == 400

    #
    # Mock raising a ValueError and assert handling with a 400 BAD REQUEST response
    sentinel.kafka_consumer.get_message_from_kafka_cb = CoroutineMock(side_effect=ValueError('Test bad response'))
    async with async_test_client as atc:
        actual_response = await atc.get('/data',
                                        params={
                                           'dataformat': 'some_topic',
                                           'partition': 0,
                                           'offset': 123
                                        })

    assert actual_response.status_code == 400
    actual_json = actual_response.json()
    assert actual_json['detail'] == 'Test bad response'

    #
    # Mock raising a KafkaMessageNotFoundError and assert handling with a 404 NOT_FOUND response
    sentinel.kafka_consumer.get_message_from_kafka_cb = \
        CoroutineMock(side_effect=KafkaMessageNotFoundError('Data record not found'))
    async with async_test_client as atc:
        actual_response = await atc.get('/data',
                                        params={
                                           'dataformat': 'some_topic',
                                           'partition': 1,
                                           'offset': 999
                                        })

    assert actual_response.status_code == 404
    actual_json = actual_response.json()
    assert actual_json['detail'] == 'Data record not found'

    #
    # Mock raising a KafkaException and assert handling with a 500 ISE response
    sentinel.kafka_consumer.get_message_from_kafka_cb = \
        CoroutineMock(side_effect=KafkaException('KafkaConsumer exception'))
    async with async_test_client as atc:
        actual_response = await atc.get('/data',
                                        params={
                                           'dataformat': 'some_topic',
                                           'partition': 11,
                                           'offset': 2134
                                        })

    assert actual_response.status_code == 500
    actual_json = actual_response.json()
    assert actual_json['detail'] == 'KafkaConsumer exception'
