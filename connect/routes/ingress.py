"""
ingress.py

Fast API Routes for handling and querying inbound EDI data messages.
"""
from fastapi.routing import APIRouter, HTTPException
from fastapi import Body, Depends, UploadFile, File
from linuxforhealth.edi.workflows import EdiWorkflow
from linuxforhealth.edi.exceptions import EdiDataValidationException
from linuxforhealth.edi.models import EdiResult
from connect.workflows.core import CoreWorkflow
from connect.config import get_settings
from connect.routes.data import LinuxForHealthDataRecordResponse
from typing import Union, Dict

router = APIRouter()


async def _process_edi_data(
    settings, edi_data: Union[str, bytes], origin_url: str
) -> Dict:
    """
    Common processor for /ingress [POST] and /ingress [POST]/File Upload.
    Executes the EDI and Core workflows against the inbound edi data, before persisting it in Kafka.
    :param settings: The Pydantic Settings configuration
    :param edi_data: The EDI data payload.
    :return: response data (dictionary)
    """

    edi = EdiWorkflow(edi_data)
    try:
        edi_result: EdiResult = edi.run()
    except EdiDataValidationException as ex:
        raise HTTPException(status_code=422, detail=str(ex))

    data_format = edi_result.metadata.ediMessageFormat
    if edi_result.metadata.specificationVersion:
        data_format += f"-{edi_result.metadata.specificationVersion}"

    workflow = CoreWorkflow(
        message=edi_data,
        data_format=data_format,
        lfh_id=settings.connect_lfh_id,
        operation="POST",
        origin_url=origin_url,
    )

    return await workflow.run()


@router.post("", response_model=LinuxForHealthDataRecordResponse)
async def post_edi_data(
    settings=Depends(get_settings),
    request_data: dict = Body(...),
):
    """
    Handles inbound EDI data, persisting it in Kafka and raising a sync event.

    :param settings: Connect configuration settings.
    :param request_data: Request data (dictionary)
    """
    edi_data: str = request_data.get("data")
    return await _process_edi_data(settings, edi_data, "/ingress")


@router.post("/upload", response_model=LinuxForHealthDataRecordResponse)
async def upload_edi_data(
    settings=Depends(get_settings),
    file: UploadFile = File(...),
):
    """
    Handles inbound EDI data, persisting it in Kafka and raising a sync event.

    :param settings: Connect configuration settings.
    :param file: The uploaded file
    """
    edi_data: bytes = await file.read()
    return await _process_edi_data(settings, edi_data, "/ingress/upload")
