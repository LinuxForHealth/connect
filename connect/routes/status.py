"""
status.py

Implements the system /status API endpoint
"""
from fastapi import Depends
from fastapi.routing import APIRouter
from pydantic.main import BaseModel
from pydantic import constr
from connect import __version__
from connect.config import get_settings
from connect.support.availability import is_service_available
from typing import List
import time

router = APIRouter()

status_regex = '^AVAILABLE|UNAVAILABLE$'


class StatusResponse(BaseModel):
    """
    Status check response model.
    The response provides component specific and overall status information
    """
    application: str
    application_version: str
    is_reload_enabled: bool
    nats_status: constr(regex=status_regex)
    kafka_broker_status: constr(regex=status_regex)
    elapsed_time: float

    class Config:
        schema_extra = {
            'example': {
                'application': 'connect.main:app',
                'application_version': '0.25.0',
                'is_reload_enabled': False,
                'nats_status': 'AVAILABLE',
                'kafka_broker_status': 'AVAILABLE',
                'elapsed_time': 0.080413915000008
            }
        }


@router.get('', response_model=StatusResponse)
async def get_status(settings=Depends(get_settings)):
    """
    :return: the current system status
    """
    async def get_service_status(setting: List[str]) -> str:
        is_available = await is_service_available(setting)
        return 'AVAILABLE' if is_available else 'UNAVAILABLE'

    start_time = time.perf_counter()
    status_fields = {
        'application': settings.uvicorn_app,
        'application_version': __version__,
        'is_reload_enabled': settings.uvicorn_reload,
        'nats_status': await get_service_status(settings.nats_servers),
        'kafka_broker_status': await get_service_status(settings.kafka_bootstrap_servers),
        'elapsed_time': time.perf_counter() - start_time
    }
    return StatusResponse(**status_fields)
