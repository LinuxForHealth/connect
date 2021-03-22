"""
utils.py

Provides utilities used by LinuxForHealth workflow definitions.
"""
import json
import logging
import uuid
from datetime import datetime
from fastapi import Response
from httpx import AsyncClient
from pyconnect.clients import get_kafka_producer
from pyconnect.exceptions import KafkaStorageError
from pyconnect.routes.data import LinuxForHealthDataRecordResponse
from pyconnect.support.encoding import (encode_from_dict,
                                        decode_to_str)


kafka_result = None
kafka_status = None


async def persist(message: dict, origin_url: str,
                  data_format: str, start_time: datetime) -> dict:
    """
    Store the message in Kafka for persistence after converting it to the LinuxForHealth
    message format.

    :param message: The python dict for the object to be stored in Kafka
    :param origin_url: The originating endpoint url
    :param data_format: The data_format of the data being stored
    :param start_time: The transaction start time
    :return: python dict for LinuxForHealthDataRecordResponse instance with
        original object instance in data field as a byte string
    """
    logging.debug(f'persist: incoming message = {message}')
    data_encoded = encode_from_dict(message)

    msg = {
        'uuid': str(uuid.uuid4()),
        'creation_date': str(datetime.utcnow().replace(microsecond=0))+'Z',
        'consuming_endpoint_url': origin_url,
        'data_format': data_format,
        'data': data_encoded,
        'store_date': str(datetime.utcnow().replace(microsecond=0))+'Z'
    }
    msg_str = json.dumps(msg)

    kafka_producer = get_kafka_producer()
    storage_start = datetime.now()
    await kafka_producer.produce_with_callback(data_format, msg_str,
                                               on_delivery=get_kafka_result)
    storage_delta = datetime.now() - storage_start
    logging.debug(f'persist: stored resource location = {kafka_result}')

    total_time = datetime.utcnow() - start_time
    msg['elapsed_storage_time'] = str(storage_delta.total_seconds())
    msg['elapsed_total_time'] = str(total_time.total_seconds())
    msg['data_record_location'] = kafka_result
    msg['status'] = kafka_status

    lfh_message = dict(LinuxForHealthDataRecordResponse(**msg))
    logging.debug(f'persist: outgoing message = {lfh_message}')
    return lfh_message


async def persist_error(message: dict, topic: str) -> dict:
    """
    Store the message in Kafka for persistence after converting it to the LinuxForHealth
    message format.

    :param message: The python dict for the object to be stored in Kafka
    :return: python dict for the error instance stored in Kafka
    """
    logging.debug(f'persist_error: incoming message = {message}')
    msg_str = json.dumps(message)

    kafka_producer = get_kafka_producer()
    await kafka_producer.produce_with_callback(topic, msg_str,
                                               on_delivery=get_kafka_result)
    logging.debug(f'persist_error: stored resource location = {kafka_result}')

    message['data_record_location'] = kafka_result
    logging.debug(f'persist_error: outgoing message = {message}')
    return message


def get_kafka_result(err: object, msg: object):
    """
    Kafka producer callback for persist workflow step.
    :param err: If error, the error returned from Kafka.
    :param msg: If success, the topic, partition and offset of the stored message.
    """
    global kafka_result
    global kafka_status

    if err is not None:
        kafka_status = 'error'
        logging.debug(kafka_status)
        raise KafkaStorageError(f'Failed to deliver message: {str(msg)} {str(err)}')
    else:
        kafka_status = 'success'
        kafka_result = f'{msg.topic()}:{msg.partition()}:{msg.offset()}'
        logging.debug(f'Produced record to topic {msg.topic()} ' \
                      f'partition [{msg.partition()}] @ offset {msg.offset()}')


async def transmit(message: dict, response: Response,
                   verify_certs: bool, transmit_server: str):
    """
    Transmit the message to an external service via HTTP.

    :param message: The python dict for a LinuxForHealthDataRecordResponse instance containing the data to be transmitted
    :param response: The FastAPI response object
    :param verify_certs: Whether to verify certs, True/False, set at the application level in config.py
    :param transmit_server: The url of external server to transmit the data to
    """
    resource_str = decode_to_str(message['data'])
    resource = json.loads(resource_str)

    async with AsyncClient(verify=verify_certs) as client:
        result = await client.post(transmit_server, json=resource)

    response.body = result.text
    response.status_code = result.status_code

    # Merge result headers into response headers with overwrite
    for key, value in result.headers.items():
        if key not in ['Content-Length', 'Content-Language', 'Date']:
            response.headers[key] = value
