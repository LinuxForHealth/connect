"""
status.py

Implements the system /status API endpoint
"""
from fastapi import Depends
from fastapi.routing import APIRouter
from pydantic.main import BaseModel
from pyconnect import __version__
from pyconnect.config import Settings, get_settings

router = APIRouter()


class StatusResponse(BaseModel):
    """
    Status check response model.
    The response provides component specific and overall status information
    """
    application: str
    application_version: str
    is_reload_enabled: bool
    system_status: str = 'OK'
    messaging_status: str = 'OK'
    database_status: str = 'OK'

    class Config:
        schema_extra = {
            'example': {
                'application': 'pyconnect.main:app',
                'application_version': '0.25.0',
                'is_reload_enabled': False,
                'system_status': 'OK',
                'messaging_status': 'OK',
                'database_status': 'OK'
            }
        }


@router.get('', response_model=StatusResponse)
async def get_status(settings: Settings = Depends(get_settings)):
    """
    :return: the current system status
    """
    status_fields = {
        'application': settings.uvicorn_app,
        'application_version': __version__,
        'is_reload_enabled': settings.uvicorn_reload,
    }
    return StatusResponse(**status_fields)
