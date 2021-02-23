"""
persistToKafka.py

NATS subscriber that subscribes to ACTIONS.persist messages and sends each message
payload to Kafka for storage.
"""
import json
from pyconnect.clients import (get_kafka_producer,
                               get_nats_client)

# client instances
kafka_producer = None

class PersistToKafka:
    """
    Subscribes to ACTIONS.persist NATS messages and sends each message
    payload to Kafka for storage.  Before sending to Kafka, each message is formatted
    in the LinuxForHealth message format.
    """
    async def start_subscriber(self):
        global kafka_producer
        kafka_producer = get_kafka_producer()
        nc = await get_nats_client()
        sid = await nc.subscribe("ACTIONS.persist", cb=message_handler)
        return sid


async def message_handler(msg):
    subject = msg.subject
    reply = msg.reply
    data = msg.data.decode()
    print("Received a message on '{subject} {reply}': {data}".format(
          subject=subject, reply=reply, data=data))

    # TODO: massage message into the correct format

    # TODO: check to see if we can get the message version to use as the topic
    await kafka_producer.produce("FHIR_R4", data)
