"""
core.py

Provides the base LinuxForHealth workflow definition.
"""
import json
import logging
import requests
import uuid
import xworkflows
from datetime import datetime
from fastapi import Response
from pyconnect.clients import get_kafka_producer
from pyconnect.exceptions import KafkaStorageError
from pyconnect.routes.data import LinuxForHealthDataRecordResponse
from pyconnect.support.encoding import (encode_from_dict,
                                        decode_to_str)


kafka_result = None
kafka_status = None


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

    def __init__(self, message, url):
        self.message = message
        self.data_format = None
        self.origin_url = url
        self.start_time = None
        self.use_response = False


    state = CoreWorkflowDef()


    @xworkflows.transition('do_validate')
    async def validate(self):
        """
        Override to provide data validation.
        """
        pass


    @xworkflows.transition('do_transform')
    async def transform(self):
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

        input: self.message as object instance (e.g. FHIR-R4 Patient)
        output: self.message as LinuxForHealthDataRecordResponse with original object instance in
                data field as stingified json.
        """
        data = self.message
        logging.debug(f'CoreWorkflow.persist: incoming message = {data}')
        logging.debug(f'CoreWorkflow.persist: incoming message type = {type(data)}')
        data_encoded = encode_from_dict(data.dict())

        message = {
            'uuid': str(uuid.uuid4()),
            'creation_date': str(datetime.utcnow().replace(microsecond=0))+'Z',
            'consuming_endpoint_url': self.origin_url,
            'data_format': self.data_format,
            'data': data_encoded,
            'store_date': str(datetime.utcnow().replace(microsecond=0))+'Z'
        }
        msg_str = json.dumps(message)

        kafka_producer = get_kafka_producer()
        storage_start = datetime.now()
        await kafka_producer.produce_with_callback(self.data_format, msg_str,
                                                   on_delivery=get_kafka_result)
        storage_delta = datetime.now() - storage_start
        logging.debug(f'CoreWorkflow.persist: stored resource location = {kafka_result}')

        total_time = datetime.utcnow() - self.start_time
        message['elapsed_storage_time'] = str(storage_delta.total_seconds())
        message['elapsed_total_time'] = str(total_time.total_seconds())
        message['data_record_location'] = kafka_result
        message['status'] = kafka_status

        lfh_message = LinuxForHealthDataRecordResponse(**message)
        logging.debug(f'CoreWorkflow.persist: outgoing message = {lfh_message}')
        self.message = lfh_message


    @xworkflows.transition('do_transmit')
    async def transmit(self, response: Response):
        """
        Transmit the message to an external service via HTTP,
        if self.transmit_server is defined by the workflow.

        inputs: self.message as object instance (e.g. FHIR-R4 Patient)
                self.transmit_server as the URL of the server to POST the fhir resource to, if defined
        output: self.message as the result of the POST to the external fhir server.
        """
        if hasattr(self, 'transmit_server'):
            resource_str = decode_to_str(self.message.data)
            resource = json.loads(resource_str)
            resource_type = resource['resourceType']
            url = self.transmit_server+'/'+resource_type

            result = requests.post(url, json=resource, verify=False)

            # Set results from Starlette response in FASTAPI response
            response.body = result.text
            response.status_code = result.status_code

            # Merge Starlette headers into FastAPI headers with overwrite
            for key, value in result.headers.items():
                if not key in ['Content-Length', 'Content-Language', 'Date']:
                    response.headers[key] = value

            self.use_response = True


    @xworkflows.transition('do_sync')
    async def synchronize(self):
        """
        Send the message to a NATS subscriber for synchronization across LFH instances.
        """
        # TODO: Create default NATS subscriber for EVENTS.* and synchronize data to all subscribers
        pass


    @xworkflows.transition('handle_error')
    def error(self, error):
        """
        Send the message to a NATS subscriber to record errors.
        """
        # TODO: Create default NATS subscriber for EVENTS.errors for the local instance
        pass


    async def run(self, response: Response):
        """
        Run the workflow according to the defined states.  Override to extend or exclude states
        for a particular implementation.

        :return: the response instance, with updated body and status_code
        """
        self.start_time = datetime.utcnow()

        try:
            logging.info(f'Running CoreWorkflow, message={self.message}')
            self.validate()
            self.transform()
            await self.persist()
            self.transmit()
            self.synchronize()
            return self.message
        except Exception as ex:
            self.error(ex)
            raise


def get_kafka_result(err, msg):
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
