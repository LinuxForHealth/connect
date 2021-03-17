"""
fhir.py

Customizes the base LinuxForHealth workflow definition for FHIR resources.
"""
import logging
import xworkflows
from fhir.resources.fhirtypesvalidators import get_fhir_model_class
from pyconnect.exceptions import (MissingFhirResourceType,
                                  FhirValidationTypeError)
from pyconnect.workflows.core import CoreWorkflow


class FhirWorkflow(CoreWorkflow):
    """
    Implements a FHIR validation and storage workflow for LinuxForHealth.
    """
    @xworkflows.transition('do_validate')
    def validate(self):
        """
        Overridden to validate the incoming FHIR message by instantiating a fhir.resources
        class from the input data dictionary.  Adapted from fhir.resources fhirtypesvalidators.py

        input: self.message as a dict for FHIR-R4 json (e.g. Patient resource type)
        output: self.message as an instantiated and validated fhir.resources resource class.
        raises: MissingFhirResourceType, FhirValidationTypeError
        """
        message = self.message
        logging.debug(f'FhirWorkflow.validate: incoming message = {message}')

        resource_type = message.pop('resourceType', None)
        logging.debug(f'FhirWorkflow.validate: resource type = {resource_type}')
        if resource_type is None:
            raise MissingFhirResourceType

        model_class = get_fhir_model_class(resource_type)
        resource = model_class.parse_obj(message)

        if not isinstance(resource, model_class):
            raise FhirValidationTypeError(model_class, type(resource))

        logging.debug(f'FhirWorkflow.validate: validated resource = {resource}')
        self.message = resource
        self.data_format = resource_type.upper()
