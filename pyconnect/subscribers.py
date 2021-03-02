"""
subscribers.py

Subscriber services support internal and external transactions and may use client services.
Services instances are bound to data attributes and accessed through "get" functions.
"""
from pyconnect.clients import get_nats_client
from pyconnect.nats_subscribers.subscribers import (start_persist_kafka_subscriber,
                                                    start_validate_fhir_subscriber)


# client instances
nats_client = None
nats_subscribers = []


async def create_nats_subscribers():
    """
    Create an instance of each NATS subscriber.  Add additional subscribers as needed.
    """
    subscriber = await start_persist_kafka_subscriber()
    nats_subscribers.append(subscriber)
    subscriber = await start_validate_fhir_subscriber()
    nats_subscribers.append(subscriber)


async def remove_nats_subscribers():
    """
    Remove all NATS subscribers
    """

    nats_client = await get_nats_client()
    for subscriber in nats_subscribers:
        nats_client.unsubscribe(subscriber)
