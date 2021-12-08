"""
nats.py
NATS message subscribers and message handlers
"""
import asyncio
import connect.workflows.core as core
import json
import logging
import nats
import os
import ssl
from datetime import datetime
from httpx import AsyncClient
from nats.aio.client import Client as NatsClient
from nats.aio.msg import Msg
from nats.js import JetStreamContext
from nats.js.api import RetentionPolicy, StorageType
from typing import Callable, List, Optional
from connect.clients.kafka import get_kafka_producer, KafkaCallback
from connect.config import (
    get_settings,
    get_ssl_context,
    nats_timing_subject,
    nats_timing_consumer,
    nats_sync_subject,
    nats_sync_consumer,
    nats_retransmit_subject,
    nats_retransmit_consumer,
    nats_app_sync_subject,
    nats_app_sync_consumer,
    kafka_sync_topic,
)
from connect.support.encoding import (
    decode_to_dict,
    decode_to_str,
    ConnectEncoder,
)


logger = logging.getLogger(__name__)
nats_client = None
nats_clients = []
jetstream_context = None
timing_metrics = {}
nats_retransmit_queue = []
nats_retransmit_canceled = False
retransmit_task = None


async def create_nats_subscribers():
    """
    Create NATS subscribers.  Add additional subscribers as needed.
    """
    await start_sync_event_subscribers()
    await start_local_subscriber(
        nats_timing_consumer, nats_timing_event_handler, "EVENTS", "TIMING"
    )
    await start_local_subscriber(
        nats_retransmit_consumer, nats_retransmit_event_handler, "EVENTS", "RETRANSMIT"
    )

    retransmit_loop = asyncio.get_event_loop()
    global retransmit_task
    retransmit_task = retransmit_loop.create_task(retransmitter())


async def start_sync_event_subscribers():
    """
    Create a NATS subscriber for 'nats_sync_subject' for the local NATS server/cluster and
    for each NATS server defined by 'nats_sync_subscribers' in config.py.
    """
    settings = get_settings()

    # subscribe to nats_sync_subject from the local NATS server or cluster
    await start_local_subscriber(
        nats_sync_consumer, nats_sync_event_handler, "EVENTS", "SYNC"
    )

    # subscribe to nats_sync_subject from any additional NATS servers
    await start_subscribers(
        nats_sync_consumer,
        nats_sync_event_handler,
        settings.nats_sync_subscribers,
        "EVENTS",
        "SYNC",
    )


async def start_local_subscriber(
    subject: str, callback: Callable, stream: str, consumer: str
) -> None:
    """
    Create a NATS subscriber with the provided subject and callback,
    subscribed to events from the local NATS server/cluster.

    :param subject: the NATS subject to subscribe to
    :param callback: the callback to call when a message is received on the subscription
    :param stream: the name of the stream that the subscription will use
    :param consumer: the durable consumer associated with this subscription or None
    """
    settings = get_settings()
    js = await get_jetstream_context()
    logger.trace(f"Subscribing to subject {subject}")
    await js.subscribe(subject, cb=callback, stream=stream, durable=consumer)
    servers = ",".join(settings.nats_servers)
    logger.debug(f"Subscribed {servers} to NATS subject {subject}")


async def start_subscribers(
    subject: str, callback: Callable, servers: List[str], stream: str, consumer: str
) -> None:
    """
    Create NATS subscribers with the provided subject and callback,
    subscribed to events from the servers in the provided servers list.

    :param subject: the NATS subject to subscribe to
    :param callback: the callback to call when a message is received on the subscription
    :param servers: the list of NATS servers to subscribe to
    :param stream: the name of the stream that the subscription will use
    :param consumer: the durable consumer associated with this subscription or None
    """
    for server in servers:
        nc = await create_nats_client(server)
        js = nc.jetstream()
        await js.subscribe(subject, cb=callback, stream=stream, durable=consumer)
        nats_clients.append(nc)
        logger.debug(f"Subscribed {server} to NATS subject {subject}")


async def nats_sync_event_handler(msg: Msg):
    """
    Callback for NATS 'nats_sync_subject' messages

    :param msg: a message delivered from the NATS server
    """
    subject = msg.subject
    reply = msg.reply
    data = msg.data.decode()
    message = json.loads(data)
    logger.trace(
        f"nats_sync_event_handler: received a message with id={message['uuid']} on {subject} {reply}"
    )

    response = await msg.ack_sync()
    logger.trace(f"nats_sync_event_handler: ack response={response}")

    # Emit an app_sync message so LFH clients that are listening only for
    # messages from this LFH node will be able to get all sync'd messages
    # from all LFH nodes.
    js = await get_jetstream_context()
    await js.publish(nats_app_sync_subject, msg.data)

    # if the message is from our local LFH, don't store in kafka
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

    # set up transmit servers, if defined
    transmit_servers = []
    settings = get_settings()
    if message["data_format"].startswith("FHIR-R4_"):
        for s in settings.connect_external_fhir_servers:
            if settings.connect_generate_fhir_server_url:
                origin_url_elements = message["consuming_endpoint_url"].split("/")
                resource_type = origin_url_elements[len(origin_url_elements) - 1]
                transmit_servers.append(f"{s}/{resource_type}")
            else:
                transmit_servers.append(s)

    # perform message type-specific decoding
    if message["data_format"].startswith("X12_"):
        msg_data = decode_to_str(message["data"])
    else:
        msg_data = decode_to_dict(message["data"])

    # process the message into the local store
    workflow = core.CoreWorkflow(
        message=msg_data,
        origin_url=message["consuming_endpoint_url"],
        certificate_verify=settings.certificate_verify,
        data_format=message["data_format"],
        lfh_id=message["lfh_id"],
        transmit_servers=transmit_servers,
        do_sync=False,
        operation=message["operation"],
        do_retransmit=settings.nats_enable_retransmit,
    )

    result = await workflow.run()
    logger.trace(
        f"nats_sync_event_handler: successfully replayed nats sync message with id={message['uuid']}"
    )


async def nats_timing_event_handler(msg: Msg):
    """
    Callback for NATS TIMING messages - calculates the average run time for any function timed with @timer.

    :param msg: a message delivered from the NATS server
    """
    subject = msg.subject
    reply = msg.reply
    data = msg.data.decode()
    logger.trace(f"nats_timing_event_handler: received a message on {subject} {reply}")
    await msg.ack()

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
    message = json.loads(data)
    logger.trace(
        f"nats_retransmit_event_handler: received a message with id={message['uuid']} on {subject} {reply}"
    )

    response = await msg.ack_sync()
    logger.trace(f"nats_retransmit_event_handler: ack response={response}")

    await do_retransmit(message, -1)


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
    target_endpoint_url = message["target_endpoint_urls"][0]

    try:
        # attempt to retransmit the message
        logger.trace(
            f"do_retransmit #{message['retransmit_count']}: retransmitting to: {target_endpoint_url}"
        )
        async with AsyncClient(verify=settings.certificate_verify) as client:
            if message["operation"] == "POST":
                await client.post(target_endpoint_url, json=resource)
            elif message["operation"] == "PUT":
                await client.put(target_endpoint_url, json=resource)
            elif message["operation"] == "PATCH":
                await client.patch(target_endpoint_url, json=resource)

        # if the message came from the retransmit queue, remove it
        if not queue_pos == -1:
            nats_retransmit_queue.pop(queue_pos)
        message["status"] = "SUCCESS"
        logger.trace(
            f"do_retransmit: successfully retransmitted message with id {message['uuid']} "
            + f"after {message['retransmit_count']} retries"
        )
    except Exception as ex:
        logger.trace(f"do_retransmit: exception {type(ex)}")
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

    retransmit_task.cancel()
    tasks = [retransmit_task]
    await asyncio.gather(*tasks)


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

    :param servers: List of one or more NATS servers in the same NATS cluster.
    :return: a connected NATS client instance
    """
    settings = get_settings()

    client = await nats.connect(
        verbose=True,
        servers=servers,
        nkeys_seed=os.path.join(
            settings.connect_config_directory, settings.nats_nk_file
        ),
        tls=get_ssl_context(ssl.Purpose.SERVER_AUTH),
        allow_reconnect=settings.nats_allow_reconnect,
        max_reconnect_attempts=settings.nats_max_reconnect_attempts,
    )

    logger.info("Created NATS client")
    logger.debug(f"Created NATS client for servers = {servers}")

    return client


async def get_jetstream_context() -> Optional[JetStreamContext]:
    """
    Create or return a JetStream context for the local NATS
    server or cluster defined by 'nats_servers' in config.py.

    :return: a configured NATS JetStream context
    """
    global jetstream_context

    if not jetstream_context:
        jetstream_context = await create_jetstream_context()

    return jetstream_context


async def create_jetstream_context() -> Optional[JetStreamContext]:
    """
    Create a NATS JetStream context, streams and consumers
    in the local NATS server or cluster defined by 'nats_servers'
    in config.py.

    Important defaults used by all consumers:
    - deliver_policy: nats.js.api.DeliverPolicy.last
    - ack_policy: nats.js.api.AckPolicy.explicit
    - replay_policy: nats.js.api.ReplayPolicy.instant

    :return: a configured JetStreamContext instance
    """
    nc = await get_nats_client()

    # Create JetStream context
    js = nc.jetstream()

    # Create JetStream stream to persist messages on EVENTS.* subject
    await js.add_stream(
        name="EVENTS",
        subjects=["EVENTS.*"],
        retention=RetentionPolicy.limits,
        max_msgs=-1,
        max_bytes=-1,
        max_age=365 * 24 * 60 * 60 * 1_000_000_000,
        storage=StorageType.file,
        duplicate_window=30,
    )
    logger.trace(f"Created NATS JetStream EVENTS stream")

    # Create the JetStream push consumer for data synchronization
    await js.add_consumer(
        "EVENTS",
        durable_name="SYNC",
        deliver_subject=nats_sync_consumer,
        filter_subject=nats_sync_subject,
    )
    logger.trace(f"Created NATS JetStream SYNC consumer")

    # Create the JetStream push consumer for code timing events
    await js.add_consumer(
        "EVENTS",
        durable_name="TIMING",
        deliver_subject=nats_timing_consumer,
        filter_subject=nats_timing_subject,
    )
    logger.trace(f"Created NATS JetStream TIMING consumer")

    # Create the JetStream push consumer for retransmit messages
    await js.add_consumer(
        "EVENTS",
        durable_name="RETRANSMIT",
        deliver_subject=nats_retransmit_consumer,
        filter_subject=nats_retransmit_subject,
    )
    logger.trace(f"Created NATS JetStream RETRANSMIT consumer")

    # Create the JetStream push consumer for app sync messages
    await js.add_consumer(
        "EVENTS",
        durable_name="APP_SYNC",
        deliver_subject=nats_app_sync_consumer,
        filter_subject=nats_app_sync_subject,
    )
    logger.trace(f"Created NATS JetStream APP_SYNC consumer")

    logger.info("Created the NATS JetStream context")
    return js


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
