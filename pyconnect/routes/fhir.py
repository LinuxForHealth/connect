"""
fhir.py

Receive and store any valid FHIR data record using the /fhir [POST] endpoint.
"""
from fastapi import (Body,
                     HTTPException)
from fastapi.routing import APIRouter
from pyconnect.workflows.fhir import FhirWorkflow


router = APIRouter()


@router.post('')
async def post_fhir_data(request_data: dict = Body(...)):
    """
    Receive and process a single FHIR data record

    :param request_data: The incoming FHIR message
    :return: The resulting FHIR message
    """
    try:
        workflow = FhirWorkflow(request_data, '/fhir')
        result = await workflow.run()
        return result
    except Exception as ex:
        raise HTTPException(status_code=500, detail=ex)
