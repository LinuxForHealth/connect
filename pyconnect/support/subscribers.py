"""
subscribers.py
Subscriber services support internal and external transactions via NATS JetStream.
"""
import logging
import json
from nats.aio.client import Msg
from pyconnect.clients import get_nats_client


nats_subscribers = []


async def create_nats_subscribers():
    """
    Create an instance of each NATS subscriber.  Add additional subscribers as needed.
    """
    subscriber = await start_event_subscriber()
    nats_subscribers.append(subscriber)


async def start_event_subscriber():
    """
    Subscribes to EVENTS.responses NATS messages from the local LFH
    and any defined remote LFH instances.
    """
    nats_client = await get_nats_client()
    sid = await nats_client.subscribe("EVENTS.responses", cb=lfh_event_handler)
    return sid


async def lfh_event_handler(msg: Msg):
    """
    Callback for EVENTS.responses messages
    """
    subject = msg.subject
    reply = msg.reply
    data = msg.data.decode()
    logging.debug("Received a message on '{subject} {reply}': {data}".format(
                  subject=subject, reply=reply, data=data))

    # TODO: additional handling of events.response.


async def remove_nats_subscribers():
    """
    Remove all NATS subscribers (could be used during shutdown)
    """
    nats_client = await get_nats_client()
    for subscriber in nats_subscribers:
        nats_client.unsubscribe(subscriber)

