"""
test_fhir.py

Tests the processes and transitions defined within the FHIR Workflow implementation.
"""
import pytest
from pydantic import ValidationError

from connect.exceptions import MissingFhirResourceType, FhirValidationError
from connect.workflows.fhir import FhirWorkflow
from connect.support.timer import nats


@pytest.fixture
def workflow() -> FhirWorkflow:
    config = {
        "message": {"resourceType": "Patient", "id": "001", "active": True},
        "origin_url": "http://localhost:5000/fhir",
        "certificate_verify": False,
        "lfh_id": "90cf887d-eaa0-4997-b2b7-b1e39ae0ec03",
        "operation": "POST",
    }
    workflow = FhirWorkflow(**config)
    return workflow


@pytest.mark.asyncio
async def test_validate(workflow: FhirWorkflow, nats_client, monkeypatch):
    """
    Tests FhirWorkflow.validate where the resource is valid
    """
    with monkeypatch.context() as m:
        m.setattr(nats, "get_nats_client", nats_client)
        await workflow.validate()
        assert workflow.data_format == "FHIR-R4_PATIENT"


@pytest.mark.asyncio
async def test_validate_missing_resource_type(
    workflow: FhirWorkflow, nats_client, monkeypatch
):
    """
    Tests FhirWorkflow.validate where the resource is missing
    """
    del workflow.message["resourceType"]
    with monkeypatch.context() as m:
        m.setattr(nats, "get_nats_client", nats_client)
        with pytest.raises(MissingFhirResourceType):
            await workflow.validate()


@pytest.mark.asyncio
async def test_validate_mismatched_resource_type(
    workflow: FhirWorkflow, nats_client, monkeypatch
):
    """
    Tests FhirWorkflow.validate where the resourceType in the message does not match the actual resource
    """
    workflow.message["resourceType"] = "Encounter"
    with monkeypatch.context() as m:
        m.setattr(nats, "get_nats_client", nats_client)
        with pytest.raises(ValidationError):
            await workflow.validate()


@pytest.mark.asyncio
async def test_validate_invalid_resource_type(
    workflow: FhirWorkflow, nats_client, monkeypatch
):
    """
    Tests FhirWorkflow.validate where the resourceType in the message does not match the actual resource
    """
    workflow.message["resourceType"] = "NoSuchResourceName"
    with monkeypatch.context() as m:
        m.setattr(nats, "get_nats_client", nats_client)
        with pytest.raises(FhirValidationError):
            await workflow.validate()
