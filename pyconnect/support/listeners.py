"""
listeners.py
Kafka listener-type consumers listen for messages on Kafka topics.
"""
import logging
from asyncio import (get_event_loop,
                     get_running_loop)
from confluent_kafka import (Consumer,
                             KafkaException,
                             KafkaError,
                             Message)
from pyconnect.config import get_settings
from threading import Thread
from typing import (Callable,
                    List,
                    Optional)


logger = logging.getLogger(__name__)
kafka_listeners = []
lfh_sync_topic = 'LFH_SYNC'


def create_kafka_listeners():
    """
    Create an instance of each Kafka listener.  Add additional listeners as needed.
    """
    listener = start_sync_event_listener()
    kafka_listeners.append(listener)


def start_sync_event_listener():
    """
    Listen on the Kafka lfh_sync_topic for NATS sync messages.
    """
    kafka_listener = get_kafka_listener()
    kafka_listener.listen([lfh_sync_topic], lfh_sync_msg_handler)
    return kafka_listener


def lfh_sync_msg_handler(msg: Message):
    """
    Process NATS synchronization messages stored in Kafka in lfh_sync_topic
    """
    logger.debug(f'lfh_sync_msg_handler: received message from topic {msg.topic()}')
    logger.debug(f'lfh_sync_msg_handler: message = {msg.value()}')
    # TODO: replay message in LFH


def remove_kafka_listeners():
    """
    Stop all Kafka listeners
    """
    for listener in kafka_listeners:
        listener.close()


class ConfluentAsyncKafkaListener:
    """
    Confluent's AsyncIO Wrapper for a Kafka topic listener
    Adapted from https://github.com/confluentinc/confluent-kafka-python
    """
    def __init__(self, configs, loop=None):
        self.topics = None
        self.callback = None
        self._loop = loop or get_event_loop()
        self._consumer = Consumer(configs)
        self._cancelled = False
        self._poll_thread = Thread(target=self._poll_loop)
        self._poll_thread.start()

    def _poll_loop(self):
        while not self._cancelled:
            if self.topics and self.callback:
                msg = self._consumer.poll(timeout=1.0)
                if msg is None: continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition event
                        logger.debug(f'Listener: {msg.topic()} [{msg.partition()}] reached end at offset {msg.offset()}')
                    elif msg.error():
                        raise KafkaException(msg.error())
                else:
                    self.callback(msg)

    def close(self):
        self._cancelled = True
        self.topics = None
        self.callback = None
        self._poll_thread.join()

    def listen(self, topics: List[str], callback: Callable):
        self._consumer.subscribe(topics)
        self.topics = topics
        self.callback = callback


def get_kafka_listener() -> Optional[ConfluentAsyncKafkaListener]:
    """
    :return: a new connected ConfluentAsyncKafkaListener instance
    """
    settings = get_settings()
    listener_config = {
        'bootstrap.servers': ''.join(settings.kafka_bootstrap_servers),
        'group.id': settings.kafka_consumer_default_group_id,
        'enable.auto.commit': settings.kafka_consumer_default_enable_auto_commit
    }
    return ConfluentAsyncKafkaListener(configs=listener_config,
                                       loop=get_running_loop())
