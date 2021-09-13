"""
test_x12.py

Tests the /x12 endpoints
"""

import pytest
from connect.clients import kafka, nats
from connect.config import get_settings
from unittest.mock import AsyncMock


@pytest.fixture
def x12_fixture() -> str:
    """A sample x12 fixture for a 270/eligibility inquiry transaction"""
    return "\n".join(
        [
            "ISA*03*9876543210*01*9876543210*30*000000005      *30*12345          *131031*1147*^*00501*000000907*1*T*:~",
            "GS*HS*000000005*54321*20131031*1147*1*X*005010X279A1~",
            "ST*270*0001*005010X279A1~",
            "BHT*0022*13*10001234*20131031*1147~",
            "HL*1**20*1~",
            "NM1*PR*2*PAYER C*****PI*12345~",
            "HL*2*1*21*1~",
            "NM1*1P*1*DOE*JOHN****XX*1467857193~",
            "REF*4A*000111222~",
            "N3*123 MAIN ST.*SUITE 42~",
            "N4*SAN MATEO*CA*94401~",
            "HL*3*2*22*0~",
            "TRN*1*930000000000*9800000004*PD~",
            "NM1*IL*1*DOE*JOHN****MI*00000000001~",
            "REF*6P*0123456789~",
            "DMG*D8*19700101~",
            "DTP*291*D8*20131031~",
            "EQ*1~",
            "SE*17*0001~",
            "GE*1*1~",
            "IEA*1*000000907~",
        ]
    )


@pytest.mark.asyncio
async def test_x12_post(
    async_test_client,
    x12_fixture,
    mock_async_kafka_producer,
    monkeypatch,
    settings,
):
    """
    Tests /x12 [POST] where data is not transmitted to an external server
    :param async_test_client: HTTPX test client fixture
    :param x12_fixture: ASC X12 270 (Eligibility) Fixture
    :param mock_async_kafka_producer: Mock Kafka producer fixture
    :param monkeypatch: MonkeyPatch instance used to mock test cases
    :param settings: connect configuration settings fixture
    """
    with monkeypatch.context() as m:
        m.setattr(kafka, "ConfluentAsyncKafkaProducer", mock_async_kafka_producer)
        m.setattr(nats, "get_nats_client", AsyncMock(return_value=AsyncMock()))

        async with async_test_client as ac:
            # remove external server setting
            settings.connect_external_fhir_servers = None
            ac._transport.app.dependency_overrides[get_settings] = lambda: settings

            actual_response = await ac.post("/x12", json={"x12": x12_fixture})
            actual_json = actual_response.json()

            assert actual_response.status_code == 200
            assert len(actual_json) == 1

            json_resource = actual_json[0]
            assert json_resource["consuming_endpoint_url"] == "/x12"
            assert json_resource["data_format"] == "X12_270"
            assert json_resource["status"] == "success"
            assert json_resource["data_record_location"] == "X12_270:0:0"

            # invalid request
            error_fixture: str = x12_fixture.replace("HL*1**20*1~", "HL*1**20~")
            actual_response = await ac.post("/x12", json={"x12": error_fixture})
            assert actual_response.status_code == 422
