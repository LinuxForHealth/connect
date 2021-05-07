"""
test_status.py
Tests the /status API endpoints
"""
import pytest
from unittest.mock import AsyncMock
from connect.routes import status
from connect.clients import nats
from connect.config import get_settings


@pytest.mark.asyncio
async def test_status_get(async_test_client, settings, monkeypatch):
    """
    Tests /status [GET]
    :param async_test_client: Fast API async test client
    :param settings: Settings test fixture
    :param monkeypatch: MonkeyPatch instance used to mock test cases
    """
    with monkeypatch.context() as m:
        m.setattr(status, "is_service_available", AsyncMock(return_value=True))
        m.setattr(nats, "get_client_status", AsyncMock(return_value=True))

        async with async_test_client as ac:
            settings.uvicorn_reload = False
            ac._transport.app.dependency_overrides[get_settings] = lambda: settings
            actual_response = await ac.get("/status")

            assert actual_response.status_code == 200

            actual_json = actual_response.json()
            assert "application_version" in actual_json
            assert "elapsed_time" in actual_json
            assert actual_json["elapsed_time"] > 0.0

            expected = {
                "application": "connect.asgi:app",
                "application_version": actual_json["application_version"],
                "is_reload_enabled": False,
                "nats_client_status": "CONNECTED",
                "kafka_broker_status": "AVAILABLE",
                "elapsed_time": actual_json["elapsed_time"],
            }
            assert actual_json == expected
