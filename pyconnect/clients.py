"""
clients.py

Client services used to support internal and external transactions.
Services instances are bound to data attributes and accessed through "get" functions.
"""

import ssl
import logging
from asyncio import get_event_loop, get_running_loop
from confluent_kafka import Producer, Consumer, KafkaException, TopicPartition
from nats.aio.client import Client as NatsClient
from threading import Thread
from pyconnect.config import get_settings
from pyconnect.support.kafka_segments import combine_segments
from typing import Optional

logger = logging.getLogger(__name__)

# client instances
kafka_producer = None
nats_client = None


class ConfluentAsyncKafkaProducer:
    """
    Confluent's AsyncIO Wrapper for a Kafka Producer
    Adapted from https://github.com/confluentinc/confluent-kafka-python
    """

    def __init__(self, configs, loop=None):
        self._loop = loop or get_event_loop()
        self._producer = Producer(configs)
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
                self._loop.call_soon_threadsafe(result.set_exception,
                                                KafkaException(err))
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
    :return: a connected ConfluentAsyncKafkaProducer instance
    """
    global kafka_producer
    if not kafka_producer:
        settings = get_settings()
        producer_config = {
            'bootstrap.servers': ''.join(settings.kafka_bootstrap_servers),
            'acks': settings.kafka_producer_acks
        }
        kafka_producer = ConfluentAsyncKafkaProducer(configs=producer_config,
                                                     loop=get_running_loop())
    return kafka_producer


class ConfluentAsyncKafkaConsumer:
    """
    A high-level KafkaConsumer class in order to create mutliple instances of
    the KafkaConsumer (each require a topic_name & optional consumer_group_id).

    A default consumer_group_id as specified in config.py will be used if no
    consumer_group_id is specified at instance creation.
    """

    def __init__(self, topic_name, partition, offset, consumer_group_id=None):
        if None in (topic_name, partition, offset):
            logger.error('Init Error: No topic_name, partition or offset information '
                         'provided to KafkaConsumer')
            raise ValueError('Init Error: No topic_name, partition or offset information '
                             'provided to KafkaConsumer')

        # We pull default configs from config.py
        settings = get_settings()
        self.group_id = consumer_group_id if consumer_group_id is not None \
            else settings.kafka_consumer_default_group_id

        consumer_conf = {
            'bootstrap.servers': ''.join(settings.kafka_bootstrap_servers),
            'group.id': self.group_id,
            'auto.offset.reset': 'smallest',
            'enable.auto.commit': settings.kafka_consumer_default_enable_auto_commit,
            'enable.auto.offset.store': settings.kafka_consumer_default_enable_auto_offset_store
        }

        self.consumer = Consumer(consumer_conf)
        self.topic_name = topic_name
        self.partition = partition
        self.offset = offset
        self.poll_timeout_secs = settings.kafka_consumer_default_poll_timeout_secs

    async def get_message_from_kafka(self, callback_method):
        if self.consumer is None:
            logger.error('Kafka Consumer not initialized prior to this call')
            raise ValueError('ERROR - Consumer is not initialized')

        if callback_method is None:
            logger.error('No callback_method provided for handling of fetched message segment')
            raise ValueError('ERROR - Consumer is not initialized')

        loop = get_running_loop()
        try:
            # This automatically sets the offset to the one provided by the user
            topic_partition = TopicPartition(self.topic_name, self.partition, self.offset)
            self.consumer.assign([topic_partition])

            # polls for exactly one record - waits for a configurable max time (seconds)
            msg = await loop.run_in_executor(None, self.consumer.poll, self.poll_timeout_secs)

            if msg.error():
                logger.error('Consumer error: {}', msg.error())
                raise KafkaException('Consumer error: code: {} - error: {}', msg.error.code(), msg.error())

            headers = msg.headers()

            if headers is None:
                message = msg.value()
            else:
                message = combine_segments(msg.value(), self._generate_header_dictionary(msg.headers()))

            if message is not None:
                await callback_method(message)
            else:
                _msg_not_found_error = 'No message was found that could be fetched for topic_name: {},' + \
                    'partition: {}, offset: {}'
                logger.error(_msg_not_found_error, self.topic_name, self.partition, self.offset)
                raise KafkaException(_msg_not_found_error, self.topic_name, self.partition, self.offset)

        except Exception as e:
            logger.exception('Exception occured in KafkaConsumer: {}', str(e), exc_info=True)
        finally:
            self.close_consumer()

    def _generate_header_dictionary(self, headers):
        headers_dict = {}
        for key, value in headers:
            headers_dict[key] = value
        return headers_dict

    def close_consumer(self):
        if self.consumer is not None:
            self.consumer.close()


async def get_nats_client() -> Optional[NatsClient]:
    """
    :return: a connected NATS client instance
    """
    global nats_client

    if not nats_client:
        settings = get_settings()

        ssl_ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
        ssl_ctx.load_verify_locations(settings.nats_rootCA_file)
        ssl_ctx.load_cert_chain(settings.nats_cert_file, settings.nats_key_file)

        nats_client = NatsClient()
        await nats_client.connect(
            servers=settings.nats_servers,
            loop=get_running_loop(),
            tls=ssl_ctx,
            allow_reconnect=settings.nats_allow_reconnect,
            max_reconnect_attempts=settings.nats_max_reconnect_attempts)

    return nats_client
