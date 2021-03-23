"""
core.py

Provides the base LinuxForHealth workflow definition.
"""

import json
import logging
import uuid
import xworkflows
from datetime import datetime
from fastapi import Response
from httpx import AsyncClient
from pyconnect.clients import get_kafka_producer
from pyconnect.exceptions import (KafkaStorageError,
                                  LFHError)
from pyconnect.routes.data import LinuxForHealthDataRecordResponse
from pyconnect.support.encoding import (encode_from_dict,
                                        decode_to_str,
                                        PyConnectEncoder)


class CoreWorkflowDef(xworkflows.Workflow):
    """
    Implements the base LinuxForHealth workflow definition.
    """
    states = (
        ('parse', "Parse"),
        ('validate', "Validate"),
        ('transform', "Transform"),
        ('persist', "Persist"),
        ('transmit', "Transmit"),
        ('sync', "Synchronize"),
        ('error', "Error")
    )

    transitions = (
        ('do_validate', 'parse', 'validate'),
        ('do_transform', 'validate', 'transform'),
        ('do_persist', ('parse', 'validate', 'transform'), 'persist'),
        ('do_transmit', 'persist', 'transmit'),
        ('do_sync', ('persist', 'transmit'), 'sync'),
        ('handle_error', ('parse', 'validate', 'transform', 'persist', 'transmit', 'sync'), 'error')
    )

    initial_state = 'parse'


class CoreWorkflow(xworkflows.WorkflowEnabled):
    """
    Implements the base LinuxForHealth workflow.
    """
    kafka_result = None
    kafka_status = None

    def __init__(self, message, url, settings):
        self.message = message
        self.data_format = None
        self.origin_url = url
        self.start_time = None
        self.use_response = False
        self.verify_certs = settings.certificate_verify
        self.lfh_exception_topic = settings.lfh_exception_topic


    state = CoreWorkflowDef()


    @xworkflows.transition('do_validate')
    def validate(self):
        """
        Override to provide data validation.
        """
        pass


    @xworkflows.transition('do_transform')
    def transform(self):
        """
        Override to transform from one form or protocol to another (e.g. HL7v2 to FHIR
        or FHIR R3 to R4).
        """
        pass


    @xworkflows.transition('do_persist')
    async def persist(self):
        """
        Store the message in Kafka for persistence after converting it to the LinuxForHealth
        message format.

        Input:
        self.message: The object to be stored in Kafka
        self.origin_url: The originating endpoint url
        self.data_format: The data_format of the data being stored
        self.start_time: The transaction start time

        Output:
        self.message: The python dict for LinuxForHealthDataRecordResponse instance with
            the original object instance in the data field as a byte string
        """
        data = self.message
        logging.debug(f'{self.__class__.__name__}: incoming message = {data}')
        logging.debug(f'{self.__class__.__name__}: incoming message type = {type(data)}')
        data_encoded = encode_from_dict(data.dict())

        message = {
            'uuid': str(uuid.uuid4()),
            'creation_date': str(datetime.utcnow().replace(microsecond=0)) + 'Z',
            'store_date': str(datetime.utcnow().replace(microsecond=0)) + 'Z',
            'consuming_endpoint_url': self.origin_url,
            'data_format': self.data_format,
            'data': data_encoded

        }
        response = LinuxForHealthDataRecordResponse(**message).json()

        kafka_producer = get_kafka_producer()
        kafka_cb = KafkaCallback()
        storage_start = datetime.now()
        await kafka_producer.produce_with_callback(self.data_format, response,
                                                   on_delivery=kafka_cb.get_kafka_result)

        storage_delta = datetime.now() - storage_start
        logging.debug(f' {self.__class__.__name__} persist: stored resource location = {kafka_cb.kafka_result}')
        total_time = datetime.utcnow() - self.start_time
        message['elapsed_storage_time'] = str(storage_delta.total_seconds())
        message['elapsed_total_time'] = str(total_time.total_seconds())
        message['data_record_location'] = kafka_cb.kafka_result
        message['status'] = kafka_cb.kafka_status

        response = LinuxForHealthDataRecordResponse(**message).dict()
        logging.debug(f'{self.__class__.__name__} persist: outgoing message = {response}')
        self.message = response


    @xworkflows.transition('do_transmit')
    async def transmit(self, response: Response):
        """
        Transmit the message to an external service via HTTP,
        if self.transmit_server is defined by the workflow.

        Input:
        self.message: The python dict for a LinuxForHealthDataRecordResponse instance
            containing the data to be transmitted
        response: The FastAPI Response object
        self.verify_certs: Whether to verify certs, True/False, set at the application level in config.py
        self.transmit_server: The url of external server to transmit the data to

        Output:
        The updated Response object
        """
        if hasattr(self, 'transmit_server'):
            resource_str = decode_to_str(self.message['data'])
            resource = json.loads(resource_str)

            async with AsyncClient(verify=self.verify_certs) as client:
                result = await client.post(self.transmit_server, json=resource)

            response.body = result.text
            response.status_code = result.status_code

            # Merge result headers into response headers with overwrite
            for key, value in result.headers.items():
                if key not in ['Content-Length', 'Content-Language', 'Date']:
                    response.headers[key] = value

            self.use_response = True


    @xworkflows.transition('do_sync')
    async def synchronize(self):
        """
        Send the message to NATS subscribers for synchronization across LFH instances.
        """
        # TODO: Create default NATS subscriber for EVENTS.* and synchronize data to all subscribers
        pass


    @xworkflows.transition('handle_error')
    async def error(self, error):
        """
        Store the message in Kafka for persistence after converting it to the LinuxForHealth
        message format.

        Input:
        self.message: The python dict for the error object to be stored in Kafka

        Output:
        self.message: The python dict for the error instance stored in Kafka
        """
        logging.debug(f'{self.__class__.__name__} error: incoming error = {error}')
        data_str = json.dumps(self.message, cls=PyConnectEncoder)
        data = json.loads(data_str)

        message = {
            'uuid': uuid.uuid4(),
            'error_date': datetime.utcnow().replace(microsecond=0),
            'error_msg': str(error),
            'data': data
        }
        error = LFHError(**message)

        kafka_producer = get_kafka_producer()
        kafka_cb = KafkaCallback()
        await kafka_producer.produce_with_callback(self.lfh_exception_topic, error.json(),
                                                   on_delivery=kafka_cb.get_kafka_result)

        logging.debug(f'{self.__class__.__name__} error: stored resource location = {kafka_cb.kafka_result}')
        message['data_record_location'] = kafka_cb.kafka_result
        error = LFHError(**message).json()
        logging.debug(f'{self.__class__.__name__} error: outgoing message = {error}')
        return error


    async def run(self, response: Response):
        """
        Run the workflow according to the defined states.  Override to extend or exclude states
        for a particular implementation.

        :return: the response instance, with updated body and status_code
        """
        self.start_time = datetime.utcnow()

        try:
            logging.info(f'Running {self.__class__.__name__}, message={self.message}')
            self.validate()
            self.transform()
            await self.persist()
            await self.transmit(response)
            await self.synchronize()
            return self.message
        except Exception as ex:
            msg = await self.error(ex)
            raise Exception(msg)


class KafkaCallback():
    """
    Store returned data from the Kafka callback
    """
    kafka_status = None
    kafka_result = None

    def get_kafka_result(self, err: object, msg: object):
        """
        Kafka producer callback for persist workflow step.
        :param err: If error, the error returned from Kafka.
        :param msg: If success, the topic, partition and offset of the stored message.
        """
        if err is not None:
            self.kafka_status = 'error'
            logging.debug(self.kafka_status)
            raise KafkaStorageError(f'Failed to deliver message: {str(msg)} {str(err)}')
        else:
            self.kafka_status = 'success'
            self.kafka_result = f'{msg.topic()}:{msg.partition()}:{msg.offset()}'
            logging.debug(f'Produced record to topic {msg.topic()} ' \
                          f'partition [{msg.partition()}] @ offset {msg.offset()}')
