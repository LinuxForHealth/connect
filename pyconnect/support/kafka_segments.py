"""
kafka_segments.py

pyConnect convenience functions to handle Kafka message segmentation
"""

import uuid
import math
import time
import logging
from pyconnect.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


def segment_message(msg, chunk_size=settings.kafka_message_chunk_size):
    """
    Utility function to segment a large message into chunks that the producer can send to the broker.
    The function yields each chunk with the relevant information that can be stored in the message headers
    one at a time by the Producer client and sent off to the broker.

    Allows for the creation of headers that uniquely identify segments by their id(uuid), msg_segment_count
    and a 1-index based counter.

    Example usage of `segment_message`:
```
        for segment, identifier, count, index in segment_message(msg, self.segment_size):
                segment_headers = {
                    ID: identifier,
                    COUNT: count,
                    INDEX: index
                }
                future = loop.create_future()
                final_headers = {**headers, **segment_headers}
                self.producer.produce(topic_to_send, segment, key=key, callback=self._kafka_callback(loop, future), headers=final_headers)
                futures.append(future)
```

    The consumer checks for the presence of message headers (with unique identifiers) and can use the
    combine_segments method to join the individual segments back into the larger message.
    """
    if type(msg) == str:
        msg_bytes = msg.encode('utf-8')
    elif type(msg) == bytes:
        msg_bytes = msg
    else:
        msg = 'Msg can only be of type bytes or string'
        logger.error(msg)
        raise ValueError(msg)
    msg_size = len(msg_bytes)
    msg_segment_count = math.ceil(msg_size/chunk_size)
    start = 0
    counter = 1
    identifier = str(uuid.uuid4()).encode('utf-8')
    while start < msg_size:
        end = start + chunk_size if start + chunk_size < msg_size else msg_size
        msg_segment = msg_bytes[start:end]
        start = end
        yield (msg_segment, identifier, str(msg_segment_count).encode('utf-8'), str(counter).encode('utf-8'))
        counter += 1


ID = 'fragment.identifier'
COUNT = 'fragment.count'
INDEX = 'fragment.index'

_message_store = {}


def combine_segments(value, headers):
    """
    Util method to re-combine chunked messages that were produced by the segment_message util function above.
    Additionally check example usage on segment_message function above to get a sense of how we could use custom
    {key: value} header dicts in order to uniquely identify semgents and recombine them.

    This function accesses and updates a common cache in `_message_store`. We purge unused semgents
    in this cache with a configurable eviction time.
    """
    identifier = headers[ID].decode('utf-8')
    count = int(headers[COUNT].decode('utf-8'))
    index = int(headers[INDEX].decode('utf-8'))

    message_segments = None
    if identifier in _message_store:
        message_segments = _message_store[identifier]
        message_segments['last_accessed'] = time.time()
    else:
        message_segments = {
            'bitset': [0 for _ in range(count)],
            'segments': [None for _ in range(count)],
            'last_accessed': time.time()
        }
        _message_store[identifier] = message_segments

    message_segments['segments'][index-1] = value
    message_segments['bitset'][index-1] = 1

    message = None
    if message_segments['bitset'] == [1 for _ in range(count)]:
        del _message_store[identifier]
        message = b''.join(message_segments['segments'])

    _purge_segments()

    return message


def _purge_segments():
    for identifier in list(_message_store.keys()):
        last_accessed = _message_store[identifier]['last_accessed']
        current_time = time.time() - settings.kafka_segments_purge_timeout
        if last_accessed < current_time:
            logger.info(f'Purging message segments with identifier: {identifier}')
            del _message_store[identifier]
