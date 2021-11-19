"""
data.py

Provides access to LinuxForHealth data records using the /data [GET] endpoint
"""
from pydantic import BaseModel, AnyUrl, constr
from fastapi.routing import APIRouter, HTTPException
from typing import Optional, List
from connect.clients.kafka import get_kafka_consumer
from connect.exceptions import KafkaMessageNotFoundError
from confluent_kafka import KafkaException
import uuid
import datetime
import json
router = APIRouter()

data_record_regex = "^[A-Za-z0-9_-]*:[0-9]*:[0-9]*$"


class LinuxForHealthDataRecordResponse(BaseModel):
    """
    LinuxForHealth Data Document stores information pertaining to a LinuxForHealth request.
    Data stored includes urls and statistics related to the receiving data endpoint, data storage,
    and data transmission.
    """

    uuid: uuid.UUID
    lfh_id: str
    operation: str
    creation_date: datetime.datetime
    store_date: datetime.datetime
    consuming_endpoint_url: str
    data: str
    data_format: str
    status: Optional[str]
    data_record_location: Optional[constr(regex=data_record_regex)]
    target_endpoint_urls: Optional[List[AnyUrl]]
    ipfs_uri: Optional[str]
    elapsed_storage_time: Optional[float]
    transmit_date: Optional[datetime.datetime]
    elapsed_transmit_time: Optional[float]
    elapsed_total_time: Optional[float]
    transmission_attributes: Optional[str]


@router.get("")
async def get_data_record(dataformat: str, partition: int, offset: int):
    """
    Returns a single data record from the LinuxForHealth data store.
    Raises relevant HTTP exceptions for:
      400 - BAD_REQUEST;
      404 - NOT_FOUND and
      500 - INTERNAL_SERVER_ERROR

    :param dataformat: The record's data format
    :param partition: The record partition
    :param offset: The record offset
    :return: LinuxForHealthDataRecordResponse
    """
    try:
        kafka_consumer = get_kafka_consumer(dataformat, partition, offset)
        return await kafka_consumer.get_message_from_kafka_cb(_fetch_data_record_cb)

    except KafkaException as ke:
        raise HTTPException(status_code=500, detail=str(ke))

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    except KafkaMessageNotFoundError as kmnfe:
        raise HTTPException(status_code=404, detail=str(kmnfe))


async def _fetch_data_record_cb(kafka_consumer_msg):
    decoded_json_dict = json.loads(
        kafka_consumer_msg
    )  # Decode message here if necessary in the future

    return decoded_json_dict
