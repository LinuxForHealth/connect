"""
fhir.py

Customizes the base LinuxForHealth workflow definition for FHIR resources.
"""
import logging
import xworkflows
from fhir.resources import construct_fhir_element
from pyconnect.exceptions import (FhirValidationTypeError,
                                  MissingFhirResourceType)
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
        resource_type = self.message.get('resourceType')
        logging.debug(f'FhirWorkflow.validate: resource type = {resource_type}')
        if resource_type is None:
            raise MissingFhirResourceType

        try:
            self.message = construct_fhir_element(resource_type, self.message)
            self.data_format = resource_type.upper()
        except LookupError as le:
            logging.exception(le)
            raise FhirValidationTypeError

        logging.debug(f'FhirWorkflow.validate: validated resource = {resource_type}')
