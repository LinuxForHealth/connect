"""
nats.py
NATS message subscribers and message handlers
"""
import asyncio
import connect.workflows.core as core
import json
import logging
import os
import ssl
from asyncio import get_running_loop
from datetime import datetime
from fastapi import Request, Response
from httpx import AsyncClient
from nats.aio.client import Client as NatsClient, Msg
from typing import Callable, List, Optional
from connect.clients.kafka import get_kafka_producer, KafkaCallback
from connect.config import (
    get_settings,
    get_ssl_context,
    nats_sync_subject,
    nats_retransmit_subject,
    nats_coverage_eligibility_topic,
    kafka_sync_topic,
)
from connect.routes.fhir import handle_fhir_resource
from connect.support.encoding import (
    decode_to_dict,
    decode_to_str,
    encode_from_dict,
    ConnectEncoder,
)


logger = logging.getLogger(__name__)
nats_client = None
nats_clients = []
timing_metrics = {}
nats_retransmit_queue = []
nats_retransmit_canceled = False


async def create_nats_subscribers():
    """
    Create NATS subscribers.  Add additional subscribers as needed.
    """
    await start_sync_event_subscribers()
    await start_subscriber("TIMING", nats_timing_event_handler)
    await start_subscriber(nats_retransmit_subject, nats_retransmit_event_handler)
    await start_subscriber(
        nats_coverage_eligibility_topic, nats_coverage_eligibility_event_handler
    )

    retransmit_loop = asyncio.get_event_loop()
    retransmit_loop.create_task(retransmitter())


async def start_sync_event_subscribers():
    """
    Create a NATS subscriber for 'nats_sync_subject' for the local NATS server/cluster and
    for each NATS server defined by 'nats_sync_subscribers' in config.py.
    """
    settings = get_settings()

    # subscribe to nats_sync_subject from the local NATS server or cluster
    await start_subscriber(nats_sync_subject, nats_sync_event_handler)

    # subscribe to nats_sync_subject from any additional NATS servers
    for server in settings.nats_sync_subscribers:
        client = await create_nats_client(server)
        await subscribe(client, nats_sync_subject, nats_sync_event_handler, server)


async def start_subscriber(subject: str, event_handler: Callable) -> None:
    """
    Create a NATS subscriber with the provided subject and callback,
    subscribed to events from the local NATS server/cluster.
    """
    settings = get_settings()
    client = await get_nats_client()
    await subscribe(client, subject, event_handler, ",".join(settings.nats_servers))


async def subscribe(client: NatsClient, subject: str, callback: Callable, servers: str):
    """
    Subscribe a NATS client to a subject.

    :param client: a connected NATS client
    :param subject: the NATS subject to subscribe to
    :param callback: the callback to call when a message is received on the subscription
    """
    await client.subscribe(subject, cb=callback)
    nats_clients.append(client)
    logger.debug(f"Subscribed {servers} to NATS subject {subject}")


async def nats_sync_event_handler(msg: Msg):
    """
    Callback for NATS 'nats_sync_subject' messages

    :param msg: a message delivered from the NATS server
    """
    subject = msg.subject
    reply = msg.reply
    data = msg.data.decode()
    logger.trace(f"nats_sync_event_handler: received a message on {subject} {reply}")

    # if the message is from our local LFH, don't store in kafka
    message = json.loads(data)
    if get_settings().connect_lfh_id == message["lfh_id"]:
        logger.trace(
            "nats_sync_event_handler: detected local LFH message, not storing in kafka",
        )
        return

    # store the message in kafka
    kafka_producer = get_kafka_producer()
    kafka_cb = KafkaCallback()
    await kafka_producer.produce_with_callback(
        kafka_sync_topic, data, on_delivery=kafka_cb.get_kafka_result
    )
    logger.trace(
        f"nats_sync_event_handler: stored msg in kafka topic {kafka_sync_topic} at {kafka_cb.kafka_result}",
    )

    if message["data_format"].startswith("X12_"):
        msg_data = decode_to_str(message["data"])
    else:
        msg_data = decode_to_dict(message["data"])
    settings = get_settings()

    # set up the FHIR server urls
    transmit_servers = []
    if message["data_format"].startswith("FHIR"):
        resource_type = msg_data["resourceType"]
        transmit_servers = [
            f"{s}/{resource_type}" for s in settings.connect_external_fhir_servers
        ]

    # process the message into the local store
    workflow = core.CoreWorkflow(
        message=msg_data,
        origin_url=message["consuming_endpoint_url"],
        certificate_verify=settings.certificate_verify,
        lfh_id=message["lfh_id"],
        data_format=message["data_format"],
        transmit_servers=transmit_servers,
        do_sync=False,
        operation=message["operation"],
        do_retransmit=settings.nats_enable_retransmit,
    )

    result = await workflow.run(Response())
    location = result["data_record_location"]
    logger.trace(
        f"nats_sync_event_handler: replayed nats sync message, data record location = {location}",
    )


def nats_timing_event_handler(msg: Msg):
    """
    Callback for NATS TIMING messages - calculates the average run time for any function timed with @timer.

    :param msg: a message delivered from the NATS server
    """
    data = msg.data.decode()

    message = json.loads(data)
    function_name = message["function"]
    global timing_metrics
    if function_name not in timing_metrics:
        timing_metrics[function_name] = {"total": 0.0, "count": 0, "average": 0.0}

    metric = timing_metrics[function_name]
    metric["total"] += message["elapsed_time"]
    metric["count"] += 1
    metric["average"] = metric["total"] / metric["count"]
    logger.trace(
        f"nats_timing_event_handler: {function_name}() average elapsed time = {metric['average']:.8f}s",
    )


async def nats_retransmit_event_handler(msg: Msg):
    """
    Callback for NATS 'nats_retransmit_subject' messages

    :param msg: a message delivered from the NATS server
    """
    subject = msg.subject
    reply = msg.reply
    data = msg.data.decode()
    logger.trace(
        f"nats_retransmit_event_handler: received a message on {subject} {reply}"
    )

    message = json.loads(data)
    await do_retransmit(message, -1)


async def nats_coverage_eligibility_event_handler(msg: Msg):
    """
    Callback for NATS coverage eligibility response messages that transmits
    the CoverageEligibilityResponse to the configured FHIR servers

    :param msg: a message delivered from the NATS server
    """
    subject = msg.subject
    reply = msg.reply
    data = msg.data.decode()
    logger.trace(
        f"nats_coverage_eligibility_event_handler: received a message on {subject} {reply}"
    )

    # transmit the CoverageEligibilityResponse to the configured FHIR servers via the FHIR workflow
    message = json.loads(data)
    settings = get_settings()
    await handle_fhir_resource(Response(), settings, message)


async def do_retransmit(message: dict, queue_pos: int):
    """
    Process messages from NATS or the nats_retransmit_queue.

    :param message: the LFH message containing the data to retransmit
    :param queue_pos: the position of the message in the queue.  queue_pos will be -1 if
        the message has not yet been queued or 0 <= queue_pos < len(nats_retransmit_queue).
    """
    global nats_retransmit_queue
    settings = get_settings()
    max_retries = settings.nats_retransmit_max_retries
    kafka_producer = get_kafka_producer()
    resource = decode_to_dict(message["data"])
    if "retransmit_count" not in message:
        message["retransmit_count"] = 0
    message["retransmit_count"] += 1

    try:
        # attempt to retransmit the message
        logger.trace(
            f"do_retransmit #{message['retransmit_count']}: retransmitting to: {message['target_endpoint_urls'][0]}"
        )
        async with AsyncClient(verify=settings.certificate_verify) as client:
            if message["operation"] == "POST":
                await client.post(message["target_endpoint_urls"][0], json=resource)
            elif message["operation"] == "PUT":
                await client.put(message["target_endpoint_urls"][0], json=resource)
            elif message["operation"] == "PATCH":
                await client.patch(message["target_endpoint_urls"][0], json=resource)

        # if the message came from the retransmit queue, remove it
        if not queue_pos == -1:
            nats_retransmit_queue.pop(queue_pos)
        message["status"] = "SUCCESS"
        logger.trace(
            f"do_retransmit: successfully retransmitted message with id {message['uuid']} "
            + f"after {message['retransmit_count']} retries"
        )
    except Exception as ex:
        logger.trace(f"do_retransmit: exception {ex}")
        if queue_pos == -1:
            nats_retransmit_queue.append(message)
            logger.trace(f"do_retransmit: queued message for retransmitter()")

        if not max_retries == -1 and message["retransmit_count"] >= max_retries:
            nats_retransmit_queue.pop(queue_pos)
            message["status"] = "FAILED"
            logger.trace(
                f"do_retransmit: failed retransmit of message with id {message['uuid']} "
                + f"after {message['retransmit_count']} retries"
            )

    # send outcome to kafka
    if message["status"] == "SUCCESS" or message["status"] == "FAILED":
        transmit_delta = datetime.now() - datetime.strptime(
            message["transmit_start"], "%Y-%m-%dT%H:%M:%S.%f"
        )
        message["elapsed_transmit_time"] = transmit_delta.total_seconds()
        message["elapsed_total_time"] += transmit_delta.total_seconds()
        await kafka_producer.produce(
            "RETRANSMIT", json.dumps(message, cls=ConnectEncoder)
        )
        logger.trace(f"do_retransmit: sent message to kafka topic RETRANSMIT")


async def retransmitter():
    """
    Process messages in nats_retransmit_queue.
    """
    global nats_retransmit_queue
    settings = get_settings()
    logger.trace("Starting retransmit loop")

    while not nats_retransmit_canceled:
        # iterate through nats_retransmit_queue
        for i in range(len(nats_retransmit_queue)):
            logger.trace(
                f"retransmitter: retransmitting from nats_retransmit_queue position {i}"
            )
            await do_retransmit(nats_retransmit_queue[i], i)
            if i + 1 < len(nats_retransmit_queue):
                await asyncio.sleep(2)
        await asyncio.sleep(settings.nats_retransmit_loop_interval_secs)


async def stop_nats_clients():
    """
    Gracefully stop all NATS clients prior to shutdown, including
    unsubscribing from all subscriptions.
    """
    for client in nats_clients:
        await client.close()

    global nats_retransmit_canceled
    nats_retransmit_canceled = True


async def get_nats_client() -> Optional[NatsClient]:
    """
    Create or return a NATS client connected to the local
    NATS server or cluster defined by 'nats_servers' in config.py.

    :return: a connected NATS client instance
    """
    global nats_client

    if not nats_client:
        settings = get_settings()
        nats_client = await create_nats_client(settings.nats_servers)
        nats_clients.append(nats_client)

    return nats_client


async def create_nats_client(servers: List[str]) -> Optional[NatsClient]:
    """
    Create a NATS client for any NATS server or NATS cluster configured to accept this installation's NKey.

    :param servers: List of one or more NATS servers.  If multiple servers are
    provided, they should be in the same NATS cluster.
    :return: a connected NATS client instance
    """
    settings = get_settings()

    client = NatsClient()
    await client.connect(
        servers=servers,
        nkeys_seed=os.path.join(
            settings.connect_config_directory, settings.nats_nk_file
        ),
        loop=get_running_loop(),
        tls=get_ssl_context(ssl.Purpose.SERVER_AUTH),
        allow_reconnect=settings.nats_allow_reconnect,
        max_reconnect_attempts=settings.nats_max_reconnect_attempts,
    )
    logger.info("Created NATS client")
    logger.debug(f"Created NATS client for servers = {servers}")

    return client


async def get_client_status() -> Optional[str]:
    """
    Check to see if the default NATS client is connected.

    :return: CONNECTED if client is connected, CONNECTING if reconnecting, NOT_CONNECTED otherwise
    """
    client = await get_nats_client()

    if client.is_connected:
        return "CONNECTED"
    elif client.is_reconnecting:
        return "CONNECTING"
    else:
        return "NOT_CONNECTED"
