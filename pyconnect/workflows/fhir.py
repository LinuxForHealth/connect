"""
fhir.py

Customizes the base LinuxForHealth workflow definition for FHIR resources.
"""
import json
import logging
import xworkflows
from pyconnect.clients import (get_nats_client)
from pyconnect.workflows.core import CoreWorkflow
from pydantic.json import pydantic_encoder


class FhirWorkflow(CoreWorkflow):
    """
    Implements a FHIR validation and storage workflow for LinuxForHealth.
    """


    @xworkflows.transition('do_validate')
    async def validate(self):
        """
        Send the message to a NATS subscriber for FHIR validation.
        """
        print("in validate, msg=", self.message)
        nats_client = await get_nats_client()
        msg_str = json.dumps(self.message, indent=2, default=pydantic_encoder)
        print("awaiting validate response")

        try:
            response = await nats_client.request("ACTIONS.validate", bytearray(msg_str, 'utf-8'), timeout=10)
            print("Received response: {message}".format(message=response.data.decode()))
        except ErrTimeout:
            print("Request timed out")

        self.message = response.data.decode()
        print("validate exit")


    async def run(self):
        """
        Run the workflow according to the defined states.  Overridden to exclude the 'transform'
        state for the FHIR workflow.
        """
        try:
            logging.info("Running FhirWorkflow, starting state=", self.state)
            await self.validate()
            await self.persist()
            await self.transmit()
            await self.synchronize()
            return self.message
        except Exception as ex:
            self.error(ex)
            raise
