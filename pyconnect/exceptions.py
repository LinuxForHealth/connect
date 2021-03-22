"""
exceptions.py

Defines LinuxForHealth exceptions.
"""
import uuid


class LFHException(Exception):
    """Base class for all LFH exceptions that implements __iter__ for serialization
    and adds the ability to record the message data for future processing"""

    def __init__(self, msg, data=None):
        super(Exception, self).__init__(msg)
        self.data = data
        self.msg = msg
        self.uuid = str(uuid.uuid4())

    def __iter__(self):
        yield 'error', self.msg
        yield 'uuid', self.uuid
        yield 'data', self.data


class MissingFhirResourceType(LFHException):
    """Raised when an input FHIR message does not contain a resourceType"""

    def __init__(self, msg=None, data=None):
        if msg is None:
            msg = "Input FHIR resource is missing resourceType"
        super(MissingFhirResourceType, self).__init__(msg, data)


class FhirValidationError(LFHException):
    """Raised when a FHIR resource instance cannot be properly validated"""

    def __init__(self, msg, data=None):
        super(FhirValidationError, self).__init__(msg, data)


class FhirValidationTypeError(FhirValidationError):
    """Raised when a FHIR resource instance cannot be properly instantiated from input"""

    def __init__(self, expected_type, actual_type, data=None):
        super(FhirValidationTypeError, self).__init__(
            msg=f'Expected an instance of {expected_type}, but got type {actual_type}',
            data=data
        )


class KafkaStorageError(LFHException):
    """Raised when storing data in Kafka fails"""

    def __init__(self, msg, data=None):
        super(KafkaStorageError, self).__init__(msg, data)


class KafkaMessageNotFoundError(LFHException):
    """Raised when a message for the specified topic, partition and offset cannot be found"""

    def __init__(self, msg, data=None):
        super(KafkaMessageNotFoundError, self).__init__(msg, data)
