"""
fhir.py

Receive and store any valid FHIR data record using the /fhir [POST] endpoint.
"""
from fastapi import (Body,
                     HTTPException)
from fastapi.routing import APIRouter
from fhir.resources.fhirtypesvalidators import get_fhir_model_class
from pyconnect.workflows.fhir import FhirWorkflow
from pyconnect.exceptions import (MissingFhirResourceType,
                                  FhirValidationTypeError)


router = APIRouter()


@router.post('')
async def post_fhir_data(request_data: dict = Body(...)):
    """
    Receive a single FHIR data record

    :param message: The incoming FHIR message
    :return: The resulting FHIR message
    """
    try:
        resource = instantiate_fhir_class(request_data)
        workflow = FhirWorkflow(resource)
        result = await workflow.run()
        return result
    except Exception as ex:
        raise HTTPException(status_code=500, detail=ex)


def instantiate_fhir_class(data: dict):
    """
    Instantiate a FHIR resource class from input data.
    Adapted from fhir.resources fhirtypesvalidators.py

    :param data: Incoming request data dictionary
    :return: FHIR resource class instance
    """
    resource_type = data.pop("resourceType", None)
    if (resource_type is None):
        raise MissingFhirResourceType

    # Use fhir.resources methods to instantiate a FHIR resource
    model_class = get_fhir_model_class(resource_type)
    resource = model_class.parse_obj(data)

    if not isinstance(resource, model_class):
        raise FhirValidationTypeError(model_class, type(resource))

    return resource
