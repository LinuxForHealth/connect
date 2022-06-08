"""
x12.py

Receive and store any valid X12 payload using the /x12 [POST] endpoint.
The endpoint parses and validates each transaction set within a X12 interchange.
Transaction sets are stored within a topic named X12_<X12 transaction code>.
Example: X12_270
"""
from pydantic import BaseModel, ValidationError
from fastapi.routing import APIRouter
from fastapi import Depends, HTTPException
from connect.config import get_settings
from connect.workflows.core import CoreWorkflow
from linuxforhealth.x12.io import X12ModelReader

router = APIRouter()


class X12Request(BaseModel):
    """X12 request model"""

    x12: str

    class Config:
        schema_extra = {
            "example": {
                "x12": "ISA*00*          *00*          *ZZ*890069730      *ZZ*154663145      *200929*1705*|*00501*000000001*0*T*:~GS*HS*890069730*154663145*20200929*1705*0001*X*005010X279A1~ST*270*0001*005010X279A1~BHT*0022*13*10001234*20200929*1319~HL*1**20*1~NM1*PR*2*UNIFIED INSURANCE CO*****PI*842610001~HL*2*1*21*1~NM1*1P*2*DOWNTOWN MEDICAL CENTER*****XX*2868383243~HL*3*2*22*0~TRN*1*1*1453915417~NM1*IL*1*PUG*LOUIS****MI*11122333301~DMG*D8*19690906~DTP*291*D8*20200101~EQ*30~SE*13*0001~GE*1*0001~IEA*1*000010216~"
            }
        }


@router.post("")
async def post_x12_data(
    x12_request: X12Request, settings=Depends(get_settings)
):

    x12_results: list = []

    try:
        with X12ModelReader(x12_request.x12) as r:
            for m in r.models():
                workflow: CoreWorkflow = CoreWorkflow(
                    message=m.x12(),
                    lfh_id=settings.connect_lfh_id,
                    origin_url="/x12",
                    operation="POST",
                    data_format="X12-5010",
                )
                results = await workflow.run()
                x12_results.append(results)
            return x12_results
    except ValidationError as ve:
        raise HTTPException(status_code=422, detail=ve)
    except Exception as ex:
        raise HTTPException(status_code=500, detail=ex)
