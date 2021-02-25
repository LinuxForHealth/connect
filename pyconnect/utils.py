import uuid
import math
import time
import sys


def segment_message(msg, chunk_size=900*1024):
    if type(msg) == str:
        msg_bytes = msg.encode('utf-8')
    elif type(msg) == bytes:
        msg_bytes = msg
    else:
        print('Msg can only be of type bytes or string', file=sys.stderr)
        raise ValueError('msg can only be of type bytes or string')
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


_SEGMENTS_PURGE_TIMEOUT = 60 * 10    # 10 mins in seconds

ID = 'fragment.identifier'
COUNT = 'fragment.count'
INDEX = 'fragment.index'

_message_store = {}


def combine_segments(value, headers):
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
        current_time = time.time() - _SEGMENTS_PURGE_TIMEOUT
        if last_accessed < current_time:
            print('Purging message segments with identifier: {}', identifier, file=sys.stdout)
            del _message_store[identifier]
