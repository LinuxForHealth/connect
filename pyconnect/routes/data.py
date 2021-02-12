"""
data.py

Provides access to LinuxForHealth data records using the /data [GET] endpoint
"""
from pydantic import (BaseModel,
                      AnyUrl,
                      constr)
from fastapi.routing import APIRouter
from typing import Optional
import uuid
import datetime

router = APIRouter()


class LinuxForHealthDataRecordResponse(BaseModel):
    """
    LinuxForHealth Data Document stores information pertaining to a LinuxForHealth request.
    Data stored includes urls and statistics related to the receiving data endpoint, data storage,
    and data transmission.
    """
    uuid: uuid.UUID
    creation_date: datetime.datetime
    store_date: datetime.datetime
    transmit_date: Optional[datetime.datetime]
    consuming_endpoint_url: AnyUrl
    data: str
    data_format: str
    status: str
    data_record_location: constr(regex='^[A-Za-z0-9_-]*:[0-9]*:[0-9]*$')
    target_endpoint_url: Optional[AnyUrl]
    elapsed_storage_time: float
    elapsed_transmit_time: float
    elapsed_total_time: float

    class Config:
        schema_extra = {
            'example': {
                'uuid': 'dbe0e8dd-7b64-4d7b-aefc-d27e2664b94a',
                'creationDate': '2021-02-12T18:13:17Z',
                'storedDate': '2021-02-12T18:14:17Z',
                'transmitDate': '2021-02-12T18:15:17Z',
                'consumingEndpointUrl': 'https://localhost:8080/endpoint',
                'dataFormat': 'EXAMPLE',
                'data': 'SGVsbG8gV29ybGQhIEl0J3MgbWUu',
                'status': 'success',
                'dataRecordLocation': 'EXAMPLE:0:0',
                'targetEndpointUrl': 'http://externalhost/endpoint',
                'elapsedStorageTime': 0.080413915000008,
                'elapsedTransmitTime': 0.080413915000008,
                'elapsedTotalTime': 0.080413915000008
            }
        }


@router.get('', response_model=LinuxForHealthDataRecordResponse)
def get_data_record(dataformat: str, partition: int, offset: int):
    """
    Returns a single data record from the LinuxForHealth data store

    :param dataformat: The record's data format
    :param partition: The record partition
    :param offset: The record offset
    :return: LinuxForHealthDataRecordResponse
    """
    # TODO: replace the mock response below with a working implementation (Kafka client)
    data_fields = {
        'uuid': 'dbe0e8dd-7b64-4d7b-aefc-d27e2664b94a',
        'creation_date': '2021-02-12T18:13:17Z',
        'store_date': '2021-02-12T18:14:17Z',
        'transmit_date': '2021-02-12T18:15:17Z',
        'consuming_endpoint_url': 'https://localhost:8080/endpoint',
        'data_format': 'EXAMPLE',
        'data': 'SGVsbG8gV29ybGQhIEl0J3MgbWUu',
        'status': 'success',
        'data_record_location': f'{dataformat}:{partition}:{offset}',
        'target_endpoint_url': 'http://externalhost/endpoint',
        'elapsed_storage_time': 0.080413915000008,
        'elapsed_transmit_time': 0.080413915000008,
        'elapsed_total_time': 0.080413915000008
    }
    data_record = LinuxForHealthDataRecordResponse(**data_fields)
    return data_record
