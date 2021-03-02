"""
core.py

Provides the base LinuxForHealth workflow definition.
"""
import json
import logging
import xworkflows
from pyconnect.clients import get_kafka_producer
from pydantic.json import pydantic_encoder


kafka_result = None


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

    def __init__(self, message):
        self.message = message


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
        Store the message in Kafka for persistence.
        """
        message = self.message
        logging.debug("CoreWorkflow.persist: incoming message = ", message)

        # TODO: convert message into the correct format for Kafka storage

        kafka_producer = get_kafka_producer()
        msg_str = json.dumps(message, indent=2, default=pydantic_encoder)
        await kafka_producer.produce_with_callback("FHIR_R4", msg_str, on_delivery=get_kafka_result)

        # TODO: add the Kafka storage offset to the final format to be returned

        logging.debug("CoreWorkflow.persist: stored resource location =", kafka_result)
        self.message = kafka_result


    @xworkflows.transition('do_transmit')
    async def transmit(self):
        """
        Transmit the message to an external service via HTTP.
        """
        # TODO: Provide default http transmission in CoreWorkflow
        pass


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


    async def run(self):
        """
        Run the workflow according to the defined states.  Override to extend or exclude states
        for a particular implementation.

        :return: the processed message
        """
        try:
            logging.info("Running CoreWorkflow, starting state=", self.state)
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
    """
    global kafka_result
    if err is not None:
        logging.debug("Failed to deliver message: %s: %s" % (str(msg), str(err)))
    else:
        kafka_result = "%s:%s:%s" % (msg.topic(), msg.partition(), msg.offset())
        logging.debug("Produced record to topic {} partition [{}] @ offset {}"
                      .format(msg.topic(), msg.partition(), msg.offset()))
