"""
fhir.py

Receive a FHIR data record using the /fhir [POST] endpoint of the form
{
    "resourceType": "Patient",
    "id": "001",
    "active": true,
    "gender": "male"
}
"""
from pydantic import (BaseModel,
                      AnyUrl,
                      constr)
from fastapi import HTTPException
from fastapi.routing import APIRouter
from pyconnect.workflows import fhir
from fhir.resources.patient import Patient

router = APIRouter()

class FhirMessage:
    """
    LinuxForHealth FhirMessage Document stores FHIR patient information.
    """

@router.post('')
def post_fhir_data(message: Patient):
    """
    Receive a single FHIR data record

    :param message: The incoming FHIR message
    :return: The FHIR message result
    """
    try:
        workflow = fhir.FhirWorkflow(message)
        return workflow.run()
    except Exception as ex:
        raise HTTPException(status_code=500, detail=ex)
