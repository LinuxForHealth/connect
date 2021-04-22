"""
exceptions.py

Defines LinuxForHealth exceptions.
"""
import datetime
import uuid
from pydantic import BaseModel, constr
from typing import Any, Optional


data_record_regex = "^[A-Za-z0-9_-]*:[0-9]*:[0-9]*$"


class LFHError(BaseModel):
    """Pydantic wrapper for any exception or error message, with the ability to include data for future processing"""

    data: Optional[Any]
    error_msg: str
    uuid: uuid.UUID
    error_date: datetime.datetime
    data_record_location: Optional[constr(regex=data_record_regex)]


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


class KafkaStorageError(Exception):
    """Raised when storing data in Kafka fails"""

    def __init__(self, msg):
        super(KafkaStorageError, self).__init__(msg)


class KafkaMessageNotFoundError(Exception):
    """Raised when a message for the specified topic, partition and offset cannot be found"""

    def __init__(self, msg):
        super(KafkaMessageNotFoundError, self).__init__(msg)
