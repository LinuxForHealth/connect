"""
test_fhir.py

Tests the processes and transitions defined within the FHIR Workflow implementation.
"""
import pytest
from pydantic import ValidationError

from pyconnect.exceptions import MissingFhirResourceType, FhirValidationError
from pyconnect.workflows.fhir import FhirWorkflow


@pytest.fixture
def workflow() -> FhirWorkflow:
    config = {
        'message': {'resourceType': 'Patient', 'id': '001', 'active': True},
        'origin_url': 'http://localhost:5000/fhir',
        'certificate_verify': False,
        'lfh_id': '90cf887d-eaa0-4997-b2b7-b1e39ae0ec03',
    }
    workflow = FhirWorkflow(**config)
    return workflow


def test_validate(workflow: FhirWorkflow):
    """
    Tests FhirWorkflow.validate where the resource is valid
    """
    workflow.validate()
    assert workflow.data_format == 'FHIR-R4_PATIENT'


def test_validate_missing_resource_type(workflow: FhirWorkflow):
    """
    Tests FhirWorkflow.validate where the resource is missing
    """
    del workflow.message['resourceType']
    with pytest.raises(MissingFhirResourceType):
        workflow.validate()


def test_validate_mismatched_resource_type(workflow: FhirWorkflow):
    """
    Tests FhirWorkflow.validate where the resourceType in the message does not match the actual resource
    """
    workflow.message['resourceType'] = 'Encounter'
    with pytest.raises(ValidationError):
        workflow.validate()


def test_validate_invalid_resource_type(workflow: FhirWorkflow):
    """
    Tests FhirWorkflow.validate where the resourceType in the message does not match the actual resource
    """
    workflow.message['resourceType'] = 'NoSuchResourceName'
    with pytest.raises(FhirValidationError):
        workflow.validate()
