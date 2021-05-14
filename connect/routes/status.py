"""
status.py

Implements the system /status API endpoint
"""
from fastapi import Depends
from fastapi.routing import APIRouter
from pydantic.main import BaseModel
from pydantic import constr
from connect import __version__
from connect.clients import nats
from connect.config import get_settings
from connect.support.availability import is_service_available
from typing import List
import time

router = APIRouter()

status_regex = "^AVAILABLE|UNAVAILABLE$"
nats_client_regex = "^CONNECTED|CONNECTING|NOT_CONNECTED$"


class StatusResponse(BaseModel):
    """
    Status check response model.
    The response provides component specific and overall status information
    """

    application: str
    application_version: str
    is_reload_enabled: bool
    nats_client_status: constr(regex=nats_client_regex)
    kafka_broker_status: constr(regex=status_regex)
    status_response_time: float
    metrics: dict

    class Config:
        schema_extra = {
            "example": {
                "application": "connect.main:app",
                "application_version": "0.25.0",
                "is_reload_enabled": False,
                "nats_client_status": "CONNECTED",
                "kafka_broker_status": "AVAILABLE",
                "status_response_time": 0.080413915000008,
                "metrics": {"run": {"total": 0.001, "count": 1, "average": 0.001}},
            }
        }


@router.get("", response_model=StatusResponse)
async def get_status(settings=Depends(get_settings)):
    """
    :return: the current system status
    """

    async def get_service_status(setting: List[str]) -> str:
        is_available = await is_service_available(setting)
        return "AVAILABLE" if is_available else "UNAVAILABLE"

    start_time = time.perf_counter()
    status_fields = {
        "application": settings.uvicorn_app,
        "application_version": __version__,
        "is_reload_enabled": settings.uvicorn_reload,
        "nats_client_status": await nats.get_client_status(),
        "kafka_broker_status": await get_service_status(
            settings.kafka_bootstrap_servers
        ),
        "status_response_time": float(
            "{:.8f}".format(time.perf_counter() - start_time)
        ),
        "metrics": format_metrics(nats.timing_metrics),
    }
    return StatusResponse(**status_fields)


def format_metrics(d: dict) -> dict:
    """
    Format the floats in a dict with nested dicts, for display.

    :param d: dict containing floats to format
    :return: new dict matching the original, except with formatted floats
    """
    new = {}

    for key in d:
        if isinstance(d[key], dict):
            new[key] = format_metrics(d[key])
        elif isinstance(d[key], float):
            new[key] = float("{:.8f}".format(d[key]))
        else:
            new[key] = d[key]

    return new
