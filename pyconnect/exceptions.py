"""
exceptions.py

Defines LinuxForHealth exceptions.

"""

class MissingFhirResourceType(Exception):
    """Raised when an input FHIR message does not contain a resourceType"""
    def __init__(self, msg=None):
        if msg is None:
            msg = "Input FHIR resource is missing resourceType"
        super(MissingFhirResourceType, self).__init__(msg)


class FhirValidationError(Exception):
    """Raised when a FHIR resource instance cannot be properly validated"""
    def __init__(self, msg):
        super(FhirValidationError, self).__init__(msg)


class FhirValidationTypeError(FhirValidationError):
    """Raised when a FHIR resource instance cannot be properly instantiated from input"""
    def __init__(self, expected_type, actual_type):
        super(FhirValidationTypeError, self).__init__(
            msg=f"Expected an instance of {expected_type}, but got type {actual_type}"
        )
