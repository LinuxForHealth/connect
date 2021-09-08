"""
test_x12.py

Tests the X12 Workflow implementation
"""
import pytest
from connect.workflows.x12 import X12Workflow
from typing import Dict, Optional
from connect.support.timer import nats
from connect.workflows import x12
from unittest.mock import AsyncMock


@pytest.fixture
def x12_fixture() -> str:
    return "\n".join(
        [
            "ISA*00*          *00*          *ZZ*890069730      *ZZ*154663145      *200929*1705*|"
            + "*00501*000000001*0*T*:~",
            "GS*HS*890069730*154663145*20200929*1705*0001*X*005010X279A1~",
            "ST*270*0001*005010X279A1~",
            "BHT*0022*13*10001234*20200929*1319~",
            "HL*1**20*1~",
            "NM1*PR*2*UNIFIED INSURANCE CO*****PI*842610001~",
            "HL*2*1*21*1~",
            "NM1*1P*2*DOWNTOWN MEDICAL CENTER*****XX*2868383243~",
            "HL*3*2*22*0~",
            "TRN*1*1*1453915417~",
            "NM1*IL*1*DOE*JOHN****MI*11122333301~",
            "DMG*D8*19800519~",
            "DTP*291*D8*20200101~",
            "EQ*30~",
            "SE*13*0001~",
            "GE*1*0001~",
            "IEA*1*000010216~",
        ]
    )


@pytest.fixture
def fhir_fixture() -> Dict:
    return {
        "resourceType": "CoverageEligibilityRequest",
        "text": {
            "status": "generated",
            "div": '<div xmlns="http://www.w3.org/1999/xhtml">A human-readable rendering of the CoverageEligibilityRequest</div>',
        },
        "status": "active",
        "priority": {"coding": [{"code": "normal"}]},
        "purpose": ["validation"],
        "patient": {
            "reference": "Patient/17bc6292c24-c8785d7f-32b0-4ebd-ba57-b7005c83c093"
        },
        "created": "2021-07-06",
        "provider": {
            "reference": "Organization/17bc6292aae-d5387fd6-86c1-409b-bc53-f8ed0779c120"
        },
        "insurer": {
            "reference": "Organization/17bc62928df-132d2ee6-9a93-44bd-acf9-46a01828c25c"
        },
        "insurance": [
            {
                "focal": True,
                "coverage": {
                    "reference": "Coverage/17bc6292ded-7935230c-4bf9-4821-b032-4afc7a1692b4"
                },
            }
        ],
    }


@pytest.fixture
def x12_workflow(x12_fixture):
    config = {
        "message": x12_fixture,
        "origin_url": "http://localhost:5000/x12",
        "certificate_verify": False,
        "lfh_id": "90cf887d-eaa0-4997-b2b7-b1e39ae0ec03",
        "operation": "POST",
        "transmit_servers": [
            "https://fhiruser:change-password@localhost:9443/fhir-server/api/v4"
        ],
    }

    return X12Workflow(**config)


async def mock_find_resource_id(
    self, client, fhir_url, resource, search: Dict
) -> Optional[str]:
    if resource == "Organization" and search["name"] == "UNIFIED INSURANCE CO":
        return "17bc62928df-132d2ee6-9a93-44bd-acf9-46a01828c25c"
    elif resource == "Organization" and search["name"] == "DOWNTOWN MEDICAL CENTER":
        return "17bc6292aae-d5387fd6-86c1-409b-bc53-f8ed0779c120"
    elif resource == "Patient" and search["name"] == ["DOE", "JOHN"]:
        return "17bc6292c24-c8785d7f-32b0-4ebd-ba57-b7005c83c093"
    elif resource == "Coverage" and search["identifier"] == "12345":
        return "17bc6292ded-7935230c-4bf9-4821-b032-4afc7a1692b4"


@pytest.mark.asyncio
async def test_transform(x12_workflow, fhir_fixture, nats_client, monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(X12Workflow, "find_resource_id", mock_find_resource_id)
        m.setattr(nats, "get_nats_client", nats_client)
        m.setattr(x12, "handle_fhir_resource", AsyncMock())
        await x12_workflow.validate()
        await x12_workflow.transform()
        assert x12_workflow.transformed_data == fhir_fixture
