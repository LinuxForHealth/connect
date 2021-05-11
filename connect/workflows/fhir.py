"""
fhir.py

Customizes the base LinuxForHealth workflow definition for FHIR resources.
"""
import logging
import xworkflows
from fhir.resources import construct_fhir_element
from connect.exceptions import FhirValidationError, MissingFhirResourceType
from connect.support.timer import sync_timer
from connect.workflows.core import CoreWorkflow


logger = logging.getLogger(__name__)


class FhirWorkflow(CoreWorkflow):
    """
    Implements a FHIR validation and storage workflow for LinuxForHealth.
    """

    @xworkflows.transition("do_validate")
    @sync_timer
    def validate(self):
        """
        Overridden to validate the incoming FHIR message by instantiating a fhir.resources
        class from the input data dictionary.  Adapted from fhir.resources fhirtypesvalidators.py

        input: self.message as a dict for FHIR-R4 json (e.g. Patient resource type)
        output: self.message as an instantiated and validated fhir.resources resource class.
        raises: MissingFhirResourceType, FhirValidationTypeError
        """
        resource_type = self.message.get("resourceType")
        logger.trace(f"FhirWorkflow.validate: resource type = {resource_type}")
        if resource_type is None:
            raise MissingFhirResourceType()

        try:
            self.message = construct_fhir_element(resource_type, self.message)
            self.data_format = f"FHIR-R4_{resource_type.upper()}"
        except LookupError as le:
            logging.exception(le)
            raise FhirValidationError(str(le))
