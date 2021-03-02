"""
subscribers.py

NATS subscriber that subscribes to ACTIONS.persist messages and sends each message
payload to Kafka for storage.
"""
import logging
import json
from fhir.resources.fhirtypesvalidators import get_fhir_model_class
from nats.aio.client import Msg
from pyconnect.clients import (get_kafka_producer,
                               get_nats_client)
from pyconnect.exceptions import (MissingFhirResourceType,
                                  FhirValidationTypeError)
from pydantic.json import pydantic_encoder


kafka_result = None


async def start_persist_kafka_subscriber():
    """
    Subscribes to ACTIONS.persist NATS messages and sends each message
    payload to Kafka for storage.  Before sending to Kafka, each message is formatted
    in the LinuxForHealth message format.
    """
    nats_client = await get_nats_client()
    sid = await nats_client.subscribe("ACTIONS.persist", cb=persist_kafka_message_handler)
    return sid


def get_kafka_result(err, msg):
    """
    Callback for Kafka producer
    """
    global kafka_result
    if err is not None:
        logging.debug("Failed to deliver message: %s: %s" % (str(msg), str(err)))
    else:
        kafka_result = "%s:%s:%s" % (msg.topic(), msg.partition(), msg.offset())
        logging.debug("Produced record to topic {} partition [{}] @ offset {}"
                     .format(msg.topic(), msg.partition(), msg.offset()))


async def persist_kafka_message_handler(msg: Msg):
    """
    Callback for ACTIONS.persist messages
    """
    subject = msg.subject
    reply = msg.reply
    data = msg.data.decode()
    logging.debug("Received a message on '{subject} {reply}': {data}".format(
                  subject=subject, reply=reply, data=data))

    # TODO: convert message into the correct format for Kafka storage

    kafka_producer = get_kafka_producer()
    await kafka_producer.produce_with_callback("FHIR_R4", data, on_delivery=get_kafka_result)

    # TODO: convert the Kafka storage result into the final format to be returned.

    nats_client = await get_nats_client()
    await nats_client.publish(reply, bytearray(kafka_result, 'utf-8'))


async def start_validate_fhir_subscriber():
    """
    Subscribes to ACTIONS.validate NATS messages and sends each message
    payload to Kafka for storage.  Before sending to Kafka, each message is formatted
    in the LinuxForHealth message format.
    """
    nats_client = await get_nats_client()
    sid = await nats_client.subscribe("ACTIONS.validate", cb=validate_fhir_message_handler)
    return sid


async def validate_fhir_message_handler(msg: Msg):
    """
    Callback for ACTIONS.validate messages

    Performs validation by instantiating a fhir.resources class from input data dictionary.
    Adapted from fhir.resources fhirtypesvalidators.py

    Result: If a validation error occurs, publishes a MissingFhirResourceType or
    FhirValidationTypeError as the response, otherwise publishes the validated
    result as the response.

    :param msg: Incoming NATS message for validation request
    """
    print("in validate_fhir_message_handler")
    subject = msg.subject
    reply = msg.reply
    data = msg.data.decode()
    print("Received a message on '{subject} {reply}': {data}".format(
        subject=subject, reply=reply, data=data))

    message = json.loads(data)
    resource_type = message.pop("resourceType", None)
    print("resource type =", resource_type)
    if resource_type is None:
        raise MissingFhirResourceType

    model_class = get_fhir_model_class(resource_type)
    resource = model_class.parse_obj(message)

    if not isinstance(resource, model_class):
        raise FhirValidationTypeError(model_class, type(resource))

    nats_client = await get_nats_client()
    msg_str = json.dumps(resource, indent=2, default=pydantic_encoder)
    await nats_client.publish(reply, bytearray(msg_str, 'utf-8'))
    print("validate_fhir_message_handler exit")
