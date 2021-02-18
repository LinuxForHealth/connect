import xworkflows
from pyconnect.workflows import core

class FhirWorkflow(core.CoreWorkflow):
    """
    Implements a FHIR validation and storage workflow for LinuxForHealth.
    """
    @xworkflows.transition('do_validate')
    def validate(self):
        # Overridden to send message to a NATS subscriber for FHIR validation
        print("Performing FHIR validation for message: ", self.message)
