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

    """
    Override to send the message to a NATS subscriber for validation.
    """
    @xworkflows.transition('do_validate')
    def validate(self): pass


    """
    Override to send the message to a NATS subscriber for transformation from one
    form or protocol to another (e.g. HL7v2 to FHIR or FHIR R3 to R4).
    """
    @xworkflows.transition('do_transform')
    def transform(self): pass


    """
    Send the message to a NATS subscriber for persistence, including transformation of
    the message to the LinuxForHealth data storage format.
    """
    @xworkflows.transition('do_persist')
    async def persist(self):
        nc = await get_nats_client()

        # json.dumps filters out all the None values in the generated resource,
        # leaving us with the message we started with. msg_str is stringified json.
        msg_str = json.dumps(self.message, indent=2, default=pydantic_encoder)
        await nc.publish("ACTIONS.persist", bytearray(msg_str, 'utf-8'))
        self.message = json.loads(msg_str)


    """
    Send the message to a NATS subscriber for transmission to an external service via HTTP.
    """
    @xworkflows.transition('do_transmit')
    def transmit(self): pass
        # TODO: Provide default http transmission in CoreWorkflow


    """
    Send the message to a NATS subscriber for synchronization across LFH instances.
    """
    @xworkflows.transition('do_sync')
    def synchronize(self): pass
        # TODO: Create default NATS subscriber for EVENTS.* and synchronize data to all subscribers

    """
    Send the message to a NATS subscriber to record errors.
    """
    @xworkflows.transition('handle_error')
    def error(self, error):
        logging.info("CoreWorkflow: Processing error: ", error)

    async def run(self):
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
