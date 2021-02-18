"""
status.py

Implements the system /status API endpoint
"""
from fastapi import Depends
from fastapi.routing import APIRouter
from pydantic.main import BaseModel
from pydantic import constr
from pyconnect import __version__
from pyconnect.config import get_settings
from pyconnect.clients import get_kafka_producer
import socket
import time

router = APIRouter()


class StatusResponse(BaseModel):
    """
    Status check response model.
    The response provides component specific and overall status information
    """
    application: str
    application_version: str
    is_reload_enabled: bool
    nats_status: constr(regex='^AVAILABLE|UNAVAILABLE$')
    nats_client_status: constr(regex='^CONNECTED|DISCONNECTED$')
    kafka_broker_status: constr(regex='^AVAILABLE|UNAVAILABLE$')
    kafka_producer_status: constr(regex='^CONNECTED|DISCONNECTED$')
    kafka_consumer_status: constr(regex='^CONNECTED|DISCONNECTED$')
    elapsed_time: float

    class Config:
        schema_extra = {
            'example': {
                'application': 'pyconnect.main:app',
                'application_version': '0.25.0',
                'is_reload_enabled': False,
                'nats_status': 'AVAILABLE',
                'nats_client_status': 'CONNECTED',
                'kafka_broker_status': 'AVAILABLE',
                'kafka_producer_status': 'CONNECTED',
                'kafka_consumer_status': 'CONNECTED',
                'elapsed_time': 0.080413915000008
            }
        }


@router.get('', response_model=StatusResponse)
async def get_status(settings=Depends(get_settings)):
                     # kafka_producer=Depends(get_kafka_producer)):
    """
    :return: the current system status
    """
    start_time = time.perf_counter()

    status_fields = {
        'application': settings.uvicorn_app,
        'application_version': __version__,
        'is_reload_enabled': settings.uvicorn_reload,
        'nats_status': 'AVAILABLE',
        'nats_client_status': 'CONNECTED',
        'kafka_broker_status': 'AVAILABLE',
        'kafka_producer_status': 'CONNECTED',
        'kafka_consumer_status': 'CONNECTED',
        'elapsed_time': time.perf_counter() - start_time
    }
    return StatusResponse(**status_fields)
