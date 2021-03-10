"""
encoding_utils.py

 pyConnect convenience functions for encoding/decoding data payloads in
 LinuxForHealth messages.
"""
import base64
import json


def encode_data_from_dict(data: dict) -> str:
    """
    Base64-encodes an object for transmission and storage.
    :param data: The dict for an object to encode
    :return: string representation of base64-encoded object
    """
    data_str = json.dumps(data)
    data_bytes = bytes(data_str, 'utf-8')
    data_encoded_bytes = base64.b64encode(data_bytes)
    data_encoded_str = str(data_encoded_bytes, 'utf-8')
    return data_encoded_str


def encode_data_from_str(data: str) -> str:
    """
    Base64-encodes a string for transmission and storage.
    :param data: The string to encode
    :return: string representation of base64-encoded string
    """
    data_bytes = bytes(data, 'utf-8')
    data_encoded_bytes = base64.b64encode(data_bytes)
    data_encoded_str = str(data_encoded_bytes, 'utf-8')
    return data_encoded_str


def encode_data_from_bytes(data: bytes) -> str:
    """
    Base64-encodes a sequence of bytes for transmission and storage.
    :param data: The byte sequence to encode
    :return: string representation of base64-encoded bytes
    """
    data_encoded_bytes = base64.b64encode(data)
    data_encoded_str = str(data_encoded_bytes, 'utf-8')
    return data_encoded_str


def decode_data_to_str(data: str) -> str:
    """
    Decodes a base64-encoded string and returns the decoded string.
    :param data: The base64-encoded string to decode
    :return: base64-decoded string
    """
    data_bytes = bytes(data, 'utf-8')
    data_decoded_bytes = base64.b64decode(data_bytes)
    data_decoded_str = str(data_decoded_bytes, 'utf-8')
    return data_decoded_str


def decode_data_to_bytes(data: str) -> bytes:
    """
    Decodes a base64-encoded string and returns a sequence of bytes.
    :param data: The base64-encoded string to decode
    :return: base64-decoded bytes
    """
    data_bytes = bytes(data, 'utf-8')
    data_decoded_bytes = base64.b64decode(data_bytes)
    return data_decoded_bytes


def decode_data_to_dict(data: str) -> dict:
    """
    Decodes a base64-encoded string and returns a sequence of bytes.
    :param data: The base64-encoded string to decode
    :return: dict for base64-decoded object
    """
    data_bytes = bytes(data, 'utf-8')
    data_decoded_bytes = base64.b64decode(data_bytes)
    data_decoded_str = str(data_decoded_bytes, 'utf-8')
    data_obj = json.loads(data_decoded_str)
    return data_obj