"""
fhir.py

Receive and store any valid FHIR data record using the /fhir [POST] endpoint.
"""
from fastapi import Body, Depends, HTTPException, Response, Request
from fastapi.routing import APIRouter
from connect.config import get_settings
from connect.workflows.fhir import FhirWorkflow
from fhir.resources.fhirtypesvalidators import MODEL_CLASSES as FHIR_RESOURCES


router = APIRouter()


@router.post("/{resource_type}")
async def post_fhir_data(
    resource_type: str,
    request: Request,
    response: Response,
    settings=Depends(get_settings),
    request_data: dict = Body(...),
):
    """
    Receive and process a single FHIR data record.  Any valid FHIR R4 may be submitted. To transmit the FHIR
    data to an external server, set fhir_r4_externalserver in connect/config.py.

    Example configuration setting:
        fhir_r4_externalserver = 'https://fhiruser:change-password@localhost:9443/fhir-server/api/v4'

    Example minimal FHIR R4 Patient resource to POST:
        {
            "resourceType": "Patient",
            "id": "001",
            "active": true
        }

    Example response, if fhir_r4_externalserver is not defined:
        Status code: 200
        Response:
            {
                "uuid": "782e1049-79ba-4899-90ec-5cf8a901261a",
                "creation_date": "2021-03-15T16:39:40+00:00",
                "store_date": "2021-03-15T16:39:40+00:00",
                "transmit_date": null,
                "consuming_endpoint_url": "/fhir",
                "data": "eyJpZCI6ICIwMDEiLCAiYWN0aXZlIjogdHJ1ZSwgImdlbmRlciI6ICJtYWxlIiwgInJlc291cmNlVHlwZSI6ICJQYXRpZW50In0=",
                "data_format": "PATIENT",
                "status": "success",
                "data_record_location": "PATIENT:0:5",
                "target_endpoint_url": null,
                "elapsed_storage_time": 0.246241,
                "elapsed_transmit_time": null,
                "elapsed_total_time": 0.292993
            }
            Note: In the above, the FHIR data posted is base64-encoded in the data field.

    Example response if fhir_r4_externalserver is set to the default FHIR server in docker-compose.yml:
        Status code: 201
        Response: None
            The actual ID used for the patient can be found in the returned location header.
            Location header example:
                'https://localhost:9443/fhir-server/api/v4/Patient/17836b8803d-87ab2979-2255-4a7b-acb8/_history/1'

    :param resource_type: Path parameter for the FHIR Resource type (Encounter, Patient, Practitioner, etc)
    :param request: The Fast API request model
    :param response: The response object which will be returned to the client
    :param settings: Connect configuration settings
    :param request_data: The incoming FHIR message
    :return: A LinuxForHealth message containing the resulting FHIR message or the
    result of transmitting to an external server, if defined
    :raise: HTTPException if the /{resource_type} is invalid or does not align with the request's resource type
    """
    if resource_type not in FHIR_RESOURCES.keys():
        raise HTTPException(status_code=404, detail=f"/{resource_type} not found")

    if resource_type != request_data.get("resourceType"):
        msg = f"request {request_data.get('resourceType')} does not match /{resource_type}"
        raise HTTPException(status_code=422, detail=msg)

    transmit_server = None
    transmission_attributes = None
    if settings.connect_external_fhir_server:
        resource_type = request_data["resourceType"]
        transmit_server = settings.connect_external_fhir_server
        if settings.connect_generate_fhir_server_url:
            transmit_server += "/" + resource_type
        transmission_attributes = {k: v for k, v in request.headers.items()}

    try:
        workflow = FhirWorkflow(
            message=request_data,
            origin_url="/fhir/" + resource_type,
            certificate_verify=settings.certificate_verify,
            lfh_id=settings.connect_lfh_id,
            transmit_server=transmit_server,
            do_sync=True,
            operation="POST",
            do_retransmit=settings.nats_enable_retransmit,
            transmission_attributes=transmission_attributes,
        )

        result = await workflow.run(response)

        if workflow.use_response:
            if not response.body:
                # properly return an empty response
                new_response = Response(status_code=response.status_code)
                new_response.headers.update(response.headers)
                return new_response
            else:
                return response
        else:
            return result
    except Exception as ex:
        raise HTTPException(status_code=500, detail=ex)
