"""
api.py

Configures the API Router for the Fast API application
"""
from fastapi import APIRouter
from pyconnect.routes import (data,
                              status,
                              fhir)

router = APIRouter()
router.include_router(data.router, prefix='/data')
router.include_router(status.router, prefix='/status')
router.include_router(fhir.router, prefix='/fhir')
