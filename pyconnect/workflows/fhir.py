"""
fhir.py

Customizes the base LinuxForHealth workflow definition for FHIR resources.
"""
import logging
import xworkflows
from pyconnect.workflows.core import CoreWorkflow
from fhir.resources.fhirtypesvalidators import get_fhir_model_class
from pyconnect.exceptions import (MissingFhirResourceType,
                                  FhirValidationTypeError)


class FhirWorkflow(CoreWorkflow):
    """
    Implements a FHIR validation and storage workflow for LinuxForHealth.
    """
    @xworkflows.transition('do_validate')
    async def validate(self):
        """
        Overridden to validate the incoming FHIR message by instantiating a fhir.resources
        class from the input data dictionary.  Adapted from fhir.resources fhirtypesvalidators.py

        Result: If a validation error occurs, raises a MissingFhirResourceType or
        FhirValidationTypeError, otherwise sets the workflow message to the validated resource.
        """
        message = self.message
        logging.debug("FhirWorkflow.validate: incoming message = ", message)

        resource_type = message.pop("resourceType", None)
        logging.debug("FhirWorkflow.validate: resource type =", resource_type)
        if resource_type is None:
            raise MissingFhirResourceType

        model_class = get_fhir_model_class(resource_type)
        resource = model_class.parse_obj(message)

        if not isinstance(resource, model_class):
            raise FhirValidationTypeError(model_class, type(resource))

        logging.debug("FhirWorkflow.validate: validated resource =", resource)
        self.message = resource


    async def run(self):
        """
        Run the workflow according to the defined states.  Overridden to exclude the
        'transform' state from the FHIR workflow.
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
