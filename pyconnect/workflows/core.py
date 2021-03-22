"""
core.py

Provides the base LinuxForHealth workflow definition.
"""
import logging
import xworkflows
from datetime import datetime
from fastapi import Response
from pyconnect.exceptions import LFHException
from pyconnect.workflows.utils import (persist,
                                       transmit,
                                       persist_error)


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

    def __init__(self, message, url, verify_certs):
        self.message = message
        self.data_format = None
        self.origin_url = url
        self.start_time = None
        self.use_response = False
        self.verify_certs = verify_certs


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
        """
        self.message = await persist(self.message.dict(), self.origin_url, self.data_format, self.start_time)


    @xworkflows.transition('do_transmit')
    async def transmit(self, response: Response):
        """
        Transmit the message to an external service via HTTP,
        if self.transmit_server is defined by the workflow.
        """
        if hasattr(self, 'transmit_server'):
            await transmit(self.message, response, self.verify_certs, self.transmit_server)
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
        Record any errors, both in the log and in Kafka.
        """
        logging.error(f'{self.__class__.__name__}: error = {error}')
        self.message = await persist_error(dict(LFHException(str(error), self.message)), 'LFHEXCEPTION')
        return self.message


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
