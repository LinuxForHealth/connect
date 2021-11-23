"""
api.py

Configures the API Router for the Fast API application
"""
from fastapi import APIRouter
from connect.routes import data, fhir, ingress, status, x12

router = APIRouter()
router.include_router(data.router, prefix="/data")
router.include_router(fhir.router, prefix="/fhir")
router.include_router(ingress.router, prefix="/ingress")
router.include_router(status.router, prefix="/status")
router.include_router(x12.router, prefix="/x12")
