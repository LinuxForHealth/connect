"""
persist_to_kafka.py

NATS subscriber that subscribes to ACTIONS.persist messages and sends each message
payload to Kafka for storage.
"""
from nats.aio.client import Msg
from pyconnect.clients import (get_kafka_producer,
                               get_nats_client)

# client instances
kafka_producer = None


"""
Subscribes to ACTIONS.persist NATS messages and sends each message
payload to Kafka for storage.  Before sending to Kafka, each message is formatted
in the LinuxForHealth message format.
"""
async def start_persist_subscriber():
    global kafka_producer
    kafka_producer = get_kafka_producer()
    nc = await get_nats_client()
    sid = await nc.subscribe("ACTIONS.persist", cb=message_handler)
    return sid


"""
Callback for ACTIONS.persist messages
"""
async def message_handler(msg: Msg):
    subject = msg.subject
    reply = msg.reply
    data = msg.data.decode()
    print("Received a message on '{subject} {reply}': {data}".format(
          subject=subject, reply=reply, data=data))

    # TODO: massage message into the correct format

    await kafka_producer.produce("FHIR_R4", data)
