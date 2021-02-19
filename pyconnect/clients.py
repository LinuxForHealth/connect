"""
clients.py

Client services used to support internal and external transactions.
Services instances are bound to data attributes and accessed through "get" functions.
"""
import asyncio
import confluent_kafka
from confluent_kafka import KafkaException
from threading import Thread
from pyconnect.config import get_settings
from typing import Optional

# client instances
async_kafka_producer = None


class ConfluentAsyncKafkaProducer:
    """
    Confluent's AsyncIO Wrapper for a Kafka Producer
    Adapted from https://github.com/confluentinc/confluent-kafka-python
    """
    def __init__(self, configs, loop=None):
        self._loop = loop or asyncio.get_event_loop()
        self._producer = confluent_kafka.Producer(configs)
        self._cancelled = False
        self._poll_thread = Thread(target=self._poll_loop)
        self._poll_thread.start()

    def _poll_loop(self):
        while not self._cancelled:
            self._producer.poll(0.1)

    def close(self):
        self._cancelled = True
        self._poll_thread.join()

    def produce(self, topic, value):
        """
        An awaitable produce method.
        """
        result = self._loop.create_future()

        def ack(err, msg):
            if err:
                self._loop.call_soon_threadsafe(result.set_exception, KafkaException(err))
            else:
                self._loop.call_soon_threadsafe(result.set_result, msg)
        self._producer.produce(topic, value, on_delivery=ack)
        return result

    def produce_with_callback(self, topic, value, on_delivery):
        """
        A produce method in which delivery notifications are made available
        via both the returned future and on_delivery callback (if specified).
        """
        result = self._loop.create_future()

        def ack(err, msg):
            if err:
                self._loop.call_soon_threadsafe(
                    result.set_exception, KafkaException(err))
            else:
                self._loop.call_soon_threadsafe(
                    result.set_result, msg)
            if on_delivery:
                self._loop.call_soon_threadsafe(
                    on_delivery, err, msg)
        self._producer.produce(topic, value, on_delivery=ack)
        return result


def get_kafka_producer() -> Optional[ConfluentAsyncKafkaProducer]:
    """
    :return: the configured ConfluentAsyncKafkaProducer instance
    """
    global async_kafka_producer
    if not async_kafka_producer:
        settings = get_settings()
        producer_config = {
            'bootstrap.servers': settings.kafka_bootstrap_servers,
            'acks': settings.kafka_producer_acks
        }
        async_kafka_producer = ConfluentAsyncKafkaProducer(configs=producer_config)
    return async_kafka_producer
