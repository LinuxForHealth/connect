"""
core.py

Provides the base LinuxForHealth workflow definition.
"""
import httpx
import json
from json import JSONDecodeError
import logging
import connect.clients.nats as nats
import uuid
from datetime import datetime
from fastapi import Response
from httpx import AsyncClient
from connect.clients.kafka import get_kafka_producer, KafkaCallback
from connect.clients.ipfs import get_ipfs_cluster_client
from connect.config import nats_sync_subject, nats_retransmit_subject
from connect.exceptions import LFHError
from connect.routes.data import LinuxForHealthDataRecordResponse
from connect.support.encoding import (
    base64_encode_value,
    decode_to_str,
    ConnectEncoder,
)
from connect.support.timer import timer
from typing import Optional, List, Dict


logger = logging.getLogger(__name__)


class CoreWorkflow:
    """
    Implements the base LinuxForHealth workflow.
    """

    def __init__(self, **kwargs):
        self.message = kwargs["message"]
        self.data_format = kwargs.get("data_format")
        self.origin_url = kwargs["origin_url"]
        self.start_time = None
        self.verify_certs = kwargs.get("certificate_verify", True)
        self.lfh_exception_topic = "LFH_EXCEPTION"
        self.lfh_id = kwargs["lfh_id"]
        self.transmit_servers = kwargs.get("transmit_servers", [])
        self.do_sync = kwargs.get("do_sync", True)
        self.uuid = str(uuid.uuid4())
        self.operation = kwargs["operation"]
        self.do_retransmit = kwargs.get("do_retransmit", True)
        self.transmission_attributes = kwargs.get("transmission_attributes", {})

    @timer
    def transform(self):
        """
        Override to transform from one form or protocol to another (e.g. HL7v2 to FHIR
        or FHIR R3 to R4).
        """
        pass

    @timer
    async def persist(self):
        """
        Store the message in IPFS and Kafka for persistence after converting it to the LinuxForHealth
        message format.

        Input:
        self.message: The object to be stored in Kafka
        self.origin_url: The originating endpoint url
        self.data_format: The data_format of the data being stored
        self.start_time: The transaction start time

        Output:
        self.message: The python dict for LinuxForHealthDataRecordResponse instance with
            the original object instance in the data field as a byte string
        """
        logger.trace(
            f"{self.__class__.__name__}: incoming message type = {type(self.message)}",
        )

        message = {
            "uuid": self.uuid,
            "lfh_id": self.lfh_id,
            "creation_date": str(datetime.utcnow().replace(microsecond=0)) + "Z",
            "store_date": str(datetime.utcnow().replace(microsecond=0)) + "Z",
            "consuming_endpoint_url": self.origin_url,
            "data_format": self.data_format,
            "data": base64_encode_value(self.message),
            "target_endpoint_urls": self.transmit_servers,
            "operation": self.operation,
            "transmission_attributes": base64_encode_value(
                self._scrub_transmission_attributes()
            ),
        }
        response = LinuxForHealthDataRecordResponse(**message)

        # Add the IPFS URI to the message
        ipfs_client = get_ipfs_cluster_client()
        response_code, cid = await ipfs_client.persist_json_to_ipfs(response.dict())
        if response_code == 200:
            message["ipfs_uri"] = "/ipfs/" + cid
            response = LinuxForHealthDataRecordResponse(**message)
        logger.trace(f"IPFS result: code={response_code} cid={cid}")

        kafka_producer = get_kafka_producer()
        kafka_cb = KafkaCallback()
        storage_start = datetime.now()
        await kafka_producer.produce_with_callback(
            self.data_format, response.json(), on_delivery=kafka_cb.get_kafka_result
        )

        storage_delta = datetime.now() - storage_start
        logger.trace(
            f" {self.__class__.__name__} persist: stored resource location = {kafka_cb.kafka_result}",
        )
        total_time = datetime.utcnow() - self.start_time
        message["elapsed_storage_time"] = storage_delta.total_seconds()
        message["elapsed_total_time"] = total_time.total_seconds()
        message["data_record_location"] = kafka_cb.kafka_result
        message["status"] = kafka_cb.kafka_status

        response = LinuxForHealthDataRecordResponse(**message).dict()
        self.message = response

    @timer
    async def transmit(self) -> Optional[List[dict]]:
        """
        :returns: If transmit servers are defined, returns an array of dicts, of the form:
            {
                "url": server,
                "result": response_body,
                "status_code": post_result.status_code,
                "headers": dict(post_result.headers.items())
            }

        Transmit the message to an external service via HTTP,
        if self.transmit_servers is defined by the workflow.

        Input:
        self.message: The python dict for a LinuxForHealthDataRecordResponse instance
            containing the data to be transmitted
        self.verify_certs: Whether to verify certs, True/False, set at the application level in config.py
        self.transmit_servers: A List of 0 or more urls to which to transmit the data

        Output:
        The updated LinuxForHealth message
        """
        if self.transmit_servers:
            resource_str = decode_to_str(self.message["data"])
            self.transmission_attributes["content-length"] = str(len(resource_str))

            transmit_start = datetime.now()
            self.message["transmit_date"] = (
                str(transmit_start.replace(microsecond=0)) + "Z"
            )
            results = []
            async with AsyncClient(verify=self.verify_certs) as client:
                for server in self.transmit_servers:
                    try:
                        post_result = await client.post(
                            server,
                            json=json.loads(resource_str),
                            headers=self.transmission_attributes,
                        )

                        if post_result.text is None:
                            response_body = None
                        else:
                            try:
                                response_body = json.loads(post_result.text)
                            except (JSONDecodeError, TypeError):
                                response_body = post_result.text

                        result = {
                            "url": server,
                            "result": response_body,
                            "status_code": post_result.status_code,
                            "headers": dict(post_result.headers.items()),
                        }
                    except Exception as ex:
                        if isinstance(ex, httpx.ConnectTimeout) or isinstance(
                            ex, httpx.ConnectError
                        ):
                            if self.do_retransmit:
                                # send retransmit message to to Kafka to record
                                # retransmit message contains only the URL that failed
                                retransmit_message = self.message
                                retransmit_message["target_endpoint_urls"] = [server]
                                retransmit_message["status"] = "ERROR"
                                kafka_producer = get_kafka_producer()
                                await kafka_producer.produce(
                                    "RETRANSMIT",
                                    json.dumps(retransmit_message, cls=ConnectEncoder),
                                )

                                # publish retransmit message to NATS
                                nats_client = await nats.get_nats_client()
                                msg_str = json.dumps(
                                    retransmit_message, cls=ConnectEncoder
                                )
                                await nats_client.publish(
                                    nats_retransmit_subject, bytearray(msg_str, "utf-8")
                                )

                        result = {
                            "url": server,
                            "result": ex,
                            "status_code": 500,
                            "headers": {},
                        }

                    results.append(result)

            transmit_delta = datetime.now() - transmit_start
            self.message["elapsed_transmit_time"] = transmit_delta.total_seconds()
            self.message["elapsed_total_time"] += transmit_delta.total_seconds()

            return results

    @timer
    async def synchronize(self):
        """
        Send the message to NATS subscribers for synchronization across LFH instances.
        """
        if self.do_sync:
            nats_client = await nats.get_nats_client()
            msg_str = json.dumps(self.message, cls=ConnectEncoder)
            await nats_client.publish(nats_sync_subject, bytearray(msg_str, "utf-8"))

    @timer
    async def error(self, error) -> str:
        """
        On error, store the error message and the current message in
        Kafka for persistence and further error handling.

        Input:
        self.message: The python dict for the current message being processed

        :param error: The error message tp be stored in kafka
        :return: The json string for the error message stored in Kafka
        """
        logger.trace(f"{self.__class__.__name__} error: incoming error = {error}")
        data_str = json.dumps(self.message, cls=ConnectEncoder)
        data = json.loads(data_str)

        message = {
            "uuid": uuid.uuid4(),
            "error_date": datetime.utcnow().replace(microsecond=0),
            "error_msg": str(error),
            "data": data,
        }
        error = LFHError(**message)

        kafka_producer = get_kafka_producer()
        kafka_cb = KafkaCallback()
        await kafka_producer.produce_with_callback(
            self.lfh_exception_topic,
            error.json(),
            on_delivery=kafka_cb.get_kafka_result,
        )
        # trace log
        logger.trace(
            f"{self.__class__.__name__} error: stored resource location = {kafka_cb.kafka_result}",
        )
        message["data_record_location"] = kafka_cb.kafka_result
        error = LFHError(**message).json()
        return error

    @timer
    async def run(self) -> Optional[dict]:
        """
        Run the workflow according to the defined states.  Override to extend or exclude states
        for a particular implementation.

        :return: dict containing the resulting LinusForHealth message and the transmit response, which may be []
        """
        self.start_time = datetime.utcnow()

        try:
            # trace log
            logger.trace(f"Running {self.__class__.__name__}")
            await self.transform()
            await self.persist()
            results = await self.transmit()
            await self.synchronize()
            return {"lfh_message": self.message, "transmit_result": results}
        except Exception as ex:
            msg = await self.error(ex)
            raise Exception(msg)

    def set_response(self, response: Response, result: dict):
        """
        Set the HTTP response based on the result of handling the message.  The result will be of the form:
            {
                "lfh_message": LinuxForHealthDataRecordResponse,
                "transmit_result": List[dict]
            }

        where lfh_message is the resulting LinuxForHealth message and transmit_result is an array of 0 or more transmit
        result dicts, of the form:
            {
                "url": str,
                "result": str,
                "status_code": int,
                "headers": dict,
            }

        :param response: The HTTP response for this HTTP request
        :param result: The LFH message and transmit results (if any)
        """
        message = result["lfh_message"]
        transmit_result = result["transmit_result"]
        json_opts = {"cls": ConnectEncoder, "indent": 4}

        if transmit_result:
            if len(transmit_result) == 1:
                response.body = json.dumps(transmit_result, **json_opts)
            else:
                response.body = json.dumps({"results": transmit_result}, **json_opts)
            response.status_code = transmit_result[0]["status_code"]
            response.headers["LinuxForHealth-MessageId"] = str(message["uuid"])
            return response
        elif message:
            return message

    def _scrub_transmission_attributes(self) -> Dict:
        """
        Removes sensitive attributes such as Authorization, Password, Token, etc
        :returns: The "scrubbed" dictionary
        """
        if not self.transmission_attributes:
            return {}

        scrubbed_attributes = {
            k: v
            for k, v in self.transmission_attributes.items()
            if "authorization" != k.lower()
            and "password" not in k.lower()
            and "pwd" not in k.lower()
            and "token" not in k.lower()
        }
        return scrubbed_attributes
