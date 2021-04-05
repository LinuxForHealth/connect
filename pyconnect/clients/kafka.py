"""
kafka.py

Client services used to support internal and external transactions.
Service instances are bound to data attributes and accessed through "get" functions.
"""
import httpx
import json
import logging
import time
from asyncio import (get_event_loop,
                     get_running_loop)
from confluent_kafka import (Producer,
                             Consumer,
                             KafkaException,
                             KafkaError,
                             Message,
                             TopicPartition)
from confluent_kafka.admin import (AdminClient,
                                   NewTopic)
from pyconnect.config import (get_settings,
                              kafka_sync_topic)
from pyconnect.exceptions import (KafkaMessageNotFoundError,
                                  KafkaStorageError)
from pyconnect.support.encoding import decode_to_dict
from threading import Thread
from typing import (Callable,
                    List,
                    Optional)


logger = logging.getLogger(__name__)
# client instances
kafka_producer = None
kafka_listeners = []

# ******************************************
# Confluent async Kafka producer and methods
# ******************************************
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


# ******************************************
# Confluent async Kafka consumer and methods
# ******************************************
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
                error_msg = f'Consumer - error: {msg.error()}'
                logger.error(error_msg)
                if(msg.error().code() is KafkaError.OFFSET_OUT_OF_RANGE):
                    raise KafkaMessageNotFoundError(error_msg)  # throw a 404 at the controller

                raise KafkaException(error_msg)

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


def get_kafka_consumer(topic_name: str,
                       partition: int,
                       offset: int = None,
                       consumer_group_id: str = None) -> ConfluentAsyncKafkaConsumer:
    """
    Main method that allows for instantiation of an async KafkaConsumer client. Accepts optional offset(long)
    value and optional consumer_group_id(string) values. If an offset is not provided, the offset would begin
    from the first available message at the specified partition.

    User is expected to call the get_message_from_kafka_cb() with a callback_method after calling this method.

    :param topic_name: The topic name for which we would be looking up a message for.
    :param partition: The partition id on which we want to look for a topic_name
    :param offset: An optional parameter to lookup a single message that exists at a specified offset
    :param consumer_group_id: An optional parameter to specify a consumer_group_id

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
        'auto.offset.reset': settings.kafka_consumer_default_auto_offset_reset,
        'enable.auto.commit': settings.kafka_consumer_default_enable_auto_commit,
        'enable.auto.offset.store': settings.kafka_consumer_default_enable_auto_offset_store
    }

    kafka_consumer = ConfluentAsyncKafkaConsumer(topic_name, partition, consumer_conf, offset, consumer_group_id)
    return kafka_consumer


# ************************************************
# Confluent async Kafka topic listener and methods
# ************************************************
class ConfluentAsyncKafkaListener:
    """
    Confluent's AsyncIO Wrapper for a Kafka topic listener
    Adapted from https://github.com/confluentinc/confluent-kafka-python
    """
    def __init__(self, configs, loop=None):
        settings = get_settings()
        self.poll_timeout = settings.kafka_listener_timeout
        self.poll_yield = settings.kafka_topics_timeout
        self.topics = None
        self.callback = None
        self._loop = loop or get_event_loop()
        self._consumer = Consumer(configs)
        self._cancelled = False
        self._poll_thread = Thread(target=self._poll_loop)
        self._poll_thread.start()

    def _poll_loop(self):
        while not self._cancelled:
            if self.topics:
                msg = self._consumer.poll(self.poll_timeout)
                if msg is None: continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition event
                        logger.debug(f'Listener: {msg.topic()} [{msg.partition()}] reached end, offset {msg.offset()}')
                    elif msg.error():
                        raise KafkaException(msg.error())
                else:
                    self.callback(msg)
            else:
                # On startup, until the topic to listen on is set,
                # we need to yield to enable proper startup.
                time.sleep(self.poll_yield)
                continue

    def close(self):
        self._cancelled = True
        self.topics = None
        self.callback = None
        self._poll_thread.join()

    def listen(self, topics: List[str], callback: Callable):
        self._consumer.subscribe(topics)
        self.callback = callback
        self.topics = topics


def create_kafka_listeners():
    """
    Create an instance of each Kafka listener.  Add additional listeners as needed.
    """
    listener = start_sync_event_listener()
    kafka_listeners.append(listener)


def start_sync_event_listener():
    """
    Listen on the Kafka kafka_sync_topic for NATS sync messages.  Create the topic if it doesn't exist.
    """
    settings = get_settings()
    client = AdminClient({'bootstrap.servers': ''.join(settings.kafka_bootstrap_servers)})
    metadata = client.list_topics()
    if metadata.topics.get(kafka_sync_topic) is None:
        new_topic = NewTopic(kafka_sync_topic,
                             num_partitions=settings.kafka_admin_new_topic_partitions,
                             replication_factor=settings.kafka_admin_new_topic_replication_factor)
        client.create_topics([new_topic])
        logger.debug(f'start_sync_event_listener: created topic = {kafka_sync_topic}')

    kafka_listener = get_kafka_listener()
    kafka_listener.listen([kafka_sync_topic], kafka_sync_msg_handler)
    logger.debug(f'start_sync_event_listener: listening for events on topic = {kafka_sync_topic}')
    return kafka_listener


def kafka_sync_msg_handler(msg: Message):
    """
    Process NATS synchronization messages stored in Kafka in kafka_sync_topic
    """
    settings = get_settings()
    logger.debug(f'kafka_sync_msg_handler: received message={msg.value()} from topic={msg.topic()}')
    msg_str = msg.value().decode()
    message = json.loads(msg_str)

    data = decode_to_dict(message['data'])
    destination_url = 'https://localhost:' + str(settings.uvicorn_port) + message['consuming_endpoint_url']

    headers = {'replay': 'True'}
    result = httpx.post(destination_url, json=data, headers=headers, verify=settings.certificate_verify)
    logger.debug(f'lfh_sync_msg_handler: posted message to {destination_url}  result = {result}')


def remove_kafka_listeners():
    """
    Stop all Kafka listeners
    """
    for listener in kafka_listeners:
        listener.close()


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


# *************************************
# Kafka callback for storage operations
# *************************************
class KafkaCallback():
    """
    Store returned data from the Kafka callback
    """

    def __init__(self):
        self.kafka_status = None
        self.kafka_result = None

    def get_kafka_result(self, err: object, msg: object):
        """
        Kafka producer callback for storage operations
        :param err: If error, the error returned from Kafka.
        :param msg: If success, the topic, partition and offset of the stored message.
        """
        if err is not None:
            self.kafka_status = 'error'
            logging.debug(self.kafka_status)
            raise KafkaStorageError(f'Failed to deliver message: {str(msg)} {str(err)}')
        else:
            self.kafka_status = 'success'
            self.kafka_result = f'{msg.topic()}:{msg.partition()}:{msg.offset()}'
            logger.debug(f'Produced record to topic {msg.topic()} '\
                         f'partition [{msg.partition()}] @ offset {msg.offset()}')
