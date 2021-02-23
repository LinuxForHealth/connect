"""
fhir.py

Receive and store any valid  FHIR data record using the /fhir [POST] endpoint.
"""
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
async def post_fhir_data(message: Patient):
    """
    Receive a single FHIR data record

    :param message: The incoming FHIR message
    :return: The FHIR message result
    """
    try:
        workflow = fhir.FhirWorkflow(message)
        result = await workflow.run()
        return result
    except Exception as ex:
        raise HTTPException(status_code=500, detail=ex)
