"""
clients.py

Client services used to support internal and external transactions.
Services instances are bound to data attributes and accessed through "get" functions.
"""

import ssl
import logging
from asyncio import (get_event_loop,
                     get_running_loop)
from confluent_kafka import (Producer,
                             Consumer,
                             KafkaException,
                             TopicPartition)
from nats.aio.client import Client as NatsClient
from threading import Thread
from pyconnect.config import get_settings
from typing import Optional
from pyconnect.exceptions import KafkaMessageNotFoundError

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
    the KafkaConsumer (each require a topic_name, partition and optional [offset and consumer_group_id]).

    The offset will start at the beginning for the partition if no offset is provided.

    A default consumer_group_id as specified in configs will be used if no
    consumer_group_id is specified at instance creation.
    """

    def __init__(self, topic_name, partition, consumer_conf, offset=None, consumer_group_id=None):

        # Check if a consumer_group_id was provided by the user; then set it
        if consumer_group_id:
            consumer_conf['group.id'] = consumer_group_id

        self.consumer = Consumer(consumer_conf)
        self.topic_name = topic_name
        self.partition = partition
        self.offset = offset

    async def get_message_from_kafka_cb(self, callback_method) -> None:
        """
        Get a specific message from the kafka_broker and invoke the callback_method automatically with the
        message body passed as an argument to the callback_method.

        :param callback_method: Takes a callback_method which is automatically called on successfully retrieving
                                a message from the KafkaBroker.
        """
        if self.consumer is None:
            logger.error('Kafka Consumer not initialized prior to this call')
            raise ValueError('ERROR - Consumer not initialized')

        if callback_method is None:
            logger.error('No callback_method provided for handling of fetched message')
            raise ValueError('ERROR - callback_method not provided')

        loop = get_running_loop()
        topic_partition = None

        try:
            # This automatically sets the offset to the one provided by the user if it is not None
            topic_partition = TopicPartition(self.topic_name, self.partition, self.offset)

            self.consumer.assign([topic_partition])

            # polls for exactly one record - waits for a configurable max time (seconds)
            msg = await loop.run_in_executor(None, self.consumer.poll, 5.0)

            if msg is None:  # Handle timeout during poll
                msg = 'Consumer error: timeout while polling message from Kafka'
                logger.error(msg)
                raise KafkaException(msg)
            if msg.error():
                logger.error(f'Consumer error: {msg.error()}')
                raise KafkaException(f'Consumer error: code: {msg.error.code()} - error: {msg.error()}')

            headers = msg.headers()
            message = None

            if headers is None:
                message = msg.value()
            # Re-evaluate later if we will need message semgentation or have a use case where the producer
            # will chunk messages and record them with the broker
            # else:
            #     message = combine_segments(msg.value(), self._generate_header_dictionary(msg.headers()))

            if message is not None:
                logger.info(f'Found message for topic_name - {self.topic_name}, partition - {self.partition} '
                            f'and offset - {self.offset}. Invoking callback_method - {callback_method}')

                return await callback_method(message)
            else:
                _msg_not_found_error = 'No message was found that could be fetched for '
                f'topic_name: {self.topic_name}, partition: {self.partition}, offset: {self.offset}'

                logger.error(_msg_not_found_error)
                raise KafkaMessageNotFoundError(_msg_not_found_error)
        finally:
            self._close_consumer()

    def _generate_header_dictionary(self, headers):
        headers_dict = {}
        for key, value in headers:
            headers_dict[key] = value
        return headers_dict

    def _close_consumer(self):
        if self.consumer is not None:
            self.consumer.close()


def get_kafka_consumer(topic_name, partition, offset=None, consumer_group_id=None) -> ConfluentAsyncKafkaConsumer:
    """
    Main method that allows for instantiation of an async KafkaConsumer client. Accepts optional offset(long)
    value and optional consumer_group_id(string) values. If an offset is not provided, the offset would begin
    from the first available message at the specified partition.

    User is expected to call the get_message_from_kafka_cb() with a callback_method after calling this method.

    :param topic_name(string): The topic name for which we would be looking up a message for.
    :param partition(int): The partition id on which we want to look for a topic_name
    :param Optional[offset(long)]: An optional parameter to lookup a single message that exists at a specified offset
    :param Optional[consumer_group_id(string)]: An optional parameter to specify a consumer_group_id

    :returns: a new instance of the ConfluentAsyncKafkaConsumer
    """
    settings = get_settings()
    if topic_name is None or partition is None:
        msg = 'Init Error: No topic_name or partition information provided.'
        logger.error(msg)
        raise ValueError(msg)

    # We pull default configs from config.py
    consumer_conf = {
        'bootstrap.servers': ''.join(settings.kafka_bootstrap_servers),
        'group.id': settings.kafka_consumer_default_group_id,
        'auto.offset.reset': 'smallest',
        'enable.auto.commit': settings.kafka_consumer_default_enable_auto_commit,
        'enable.auto.offset.store': settings.kafka_consumer_default_enable_auto_offset_store
    }

    kafka_consumer = ConfluentAsyncKafkaConsumer(topic_name, partition, consumer_conf, offset, consumer_group_id)
    return kafka_consumer


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
