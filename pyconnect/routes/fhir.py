"""
fhir.py

Receive and store any valid FHIR data record using the /fhir [POST] endpoint.
"""
from fastapi import (Body,
                     HTTPException)
from fastapi.routing import APIRouter
from fhir.resources.fhirtypesvalidators import get_fhir_model_class
from pyconnect.workflows import fhir
from pydantic.error_wrappers import ErrorWrapper, ValidationError
from pydantic.utils import ROOT_KEY


router = APIRouter()


@router.post('')
async def post_fhir_data(request_data: dict = Body(...)):
    """
    Receive a single FHIR data record

    :param message: The incoming FHIR message
    :return: The FHIR message result
    """
    try:
        resource = instantiate_fhir_class(request_data)
        workflow = fhir.FhirWorkflow(resource)
        result = await workflow.run()
        return result
    except Exception as ex:
        raise HTTPException(status_code=500, detail=ex)


def instantiate_fhir_class(data):
    """
    Adapted from fhir.resources fhirtypesvalidators.py

    :param data: Incoming request data dictionary
    :return:
    """
    resource_type = data.pop("resourceType", None)
    model_class = get_fhir_model_class(resource_type)
    resource = model_class.parse_obj(data)

    if not isinstance(resource, model_class):
        raise ValidationError(
            [
                ErrorWrapper(
                    ValueError(
                        "Value is expected from the instance of "
                        f"{model_class}, but got type {type(resource)}"
                    ),
                    loc=ROOT_KEY,
                )
            ],
            model_class,
        )

    return resource
