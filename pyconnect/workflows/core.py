"""
core.py

Provides the base LinuxForHealth workflow definition.
"""
import logging
import json
import xworkflows
from pyconnect.clients import get_nats_client
from pydantic.json import pydantic_encoder


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
        Override to send the message to a NATS subscriber for validation.
        """
        pass


    @xworkflows.transition('do_transform')
    async def transform(self):
        """
        Override to send the message to a NATS subscriber for transformation from one
        form or protocol to another (e.g. HL7v2 to FHIR or FHIR R3 to R4).
        """
        pass


    @xworkflows.transition('do_persist')
    async def persist(self):
        """
        Send the message to a NATS subscriber for persistence, including transformation of
        the message to the LinuxForHealth data storage format.
        """
        print("in persist, msg = ", self.message)
        nats_client = await get_nats_client()
        msg_str = json.dumps(self.message, indent=2, default=pydantic_encoder)

        try:
            response = await nats_client.request("ACTIONS.persist", bytearray(msg_str, 'utf-8'), timeout=10)
            print("Received response: {message}".format(message=response.data.decode()))
        except ErrTimeout:
            print("Request timed out")

        print("Received response: {message}".format(message=response.data.decode()))
        self.message = response.data.decode()
        print("persist exit")


    @xworkflows.transition('do_transmit')
    async def transmit(self):
        """
        Send the message to a NATS subscriber for transmission to an external service via HTTP.
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
        logging.info("CoreWorkflow: Processing error: ", error)


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
