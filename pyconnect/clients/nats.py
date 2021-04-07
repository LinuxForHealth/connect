"""
nats.py
NATS message subscribers and message handlers
"""
import json
import logging
import pyconnect.workflows.core as core
import ssl
from asyncio import get_running_loop
from nats.aio.client import (Client as NatsClient,
                             Msg)
from pyconnect.clients.kafka import (get_kafka_producer,
                                     KafkaCallback)
from pyconnect.config import (get_settings,
                              nats_sync_subject,
                              kafka_sync_topic)
from pyconnect.support.encoding import decode_to_dict
from typing import (Callable,
                    List,
                    Optional)


logger = logging.getLogger(__name__)
nats_client = None
nats_clients = []


async def create_nats_subscribers():
    """
    Create NATS subscribers.  Add additional subscribers as needed.
    """
    await start_sync_event_subscribers()


async def start_sync_event_subscribers():
    """
    Create a NATS subscriber for 'nats_sync_subject' for the local NATS server/cluster and
    for each NATS server defined by 'nats_sync_subscribers' in config.py.
    """
    settings = get_settings()

    # subscribe to nats_sync_subject from the local NATS server or cluster
    nats_client = await get_nats_client()
    await subscribe(nats_client, nats_sync_subject, nats_sync_event_handler, ''.join(settings.nats_servers))

    # subscribe to nats_sync_subject from any additional NATS servers
    for server in settings.nats_sync_subscribers:
        nats_client = await create_nats_client(server)
        await subscribe(nats_client, nats_sync_subject, nats_sync_event_handler, server)


async def subscribe(client: NatsClient, subject: str, callback: Callable, servers: str):
    """
    Subscribe a NATS client to a subject.

    :param client: a connected NATS client
    :param subject: the NATS subject to subscribe to
    :param callback: the callback to call when a message is received on the subscription
    """
    await client.subscribe(subject, cb=callback)
    nats_clients.append(client)
    logger.debug(f'Subscribed {servers} to NATS subject {subject}')


async def nats_sync_event_handler(msg: Msg):
    """
    Callback for NATS 'nats_sync_subject' messages
    """
    subject = msg.subject
    reply = msg.reply
    data = msg.data.decode()
    logger.debug(f'nats_sync_event_handler: received a message on {subject} {reply}: {data}')

    # if the message is from our local LFH, don't store in kafka
    message = json.loads(data)
    if (get_settings().lfh_id == message['lfh_id']):
        logger.debug('nats_sync_event_handler: detected local LFH message, not storing in kafka')
        return

    # store the message in kafka
    kafka_producer = get_kafka_producer()
    kafka_cb = KafkaCallback()
    await kafka_producer.produce_with_callback(kafka_sync_topic, data,
                                               on_delivery=kafka_cb.get_kafka_result)
    logger.debug(f'nats_sync_event_handler: stored msg in kafka topic {kafka_sync_topic} at {kafka_cb.kafka_result}')

    # process the message into the local store
    settings = get_settings()
    msg_data = decode_to_dict(message['data'])
    workflow = core.CoreWorkflow(message=msg_data,
                                 origin_url=message['consuming_endpoint_url'],
                                 certificate_verify=settings.certificate_verify,
                                 lfh_id=message['lfh_id'],
                                 data_format=message['data_format'],
                                 transmit_server=None,
                                 do_sync=False)

    result = await workflow.run(None)
    location = result['data_record_location']
    logger.debug(f'nats_sync_event_handler: replayed nats sync message, data record location = {location}')


async def stop_nats_clients():
    '''
    Gracefully stop all NATS clients prior to shutdown, including
    unsubscribing from all subscriptions.
    '''
    for client in nats_clients:
        await client.close()


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
    Create a NATS client for any NATS server or NATS cluster.

    :param servers: List of one or more NATS servers.  If multiple servers are
    provided, they should be in the same NATS cluster.
    :return: a connected NATS client instance
    """
    settings = get_settings()

    ssl_ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
    ssl_ctx.load_verify_locations(settings.nats_rootCA_file)

    nats_client = NatsClient()
    await nats_client.connect(
        servers=servers,
        loop=get_running_loop(),
        tls=ssl_ctx,
        allow_reconnect=settings.nats_allow_reconnect,
        max_reconnect_attempts=settings.nats_max_reconnect_attempts)
    logger.debug(f'Created NATS client for servers = {servers}')

    return nats_client
