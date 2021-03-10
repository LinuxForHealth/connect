"""
test_encoding_utils.py

Tests pyConnect support base64 encoding convenience functions
"""
from pyconnect.support.encoding import (encode_from_dict,
                                        encode_from_str,
                                        encode_from_bytes,
                                        decode_to_str,
                                        decode_to_bytes,
                                        decode_to_dict)


def test_encode_from_dict():
    """
    Validates encode_from_dict with mock data.
    """
    actual_data = {
        "resourceType": "Patient",
        "id": "001",
        "active": True
    }
    encoded_data = encode_from_dict(actual_data)
    expected_data = 'eyJyZXNvdXJjZVR5cGUiOiAiUGF0aWVudCIsICJpZCI6ICIwMDEiLCAiYWN0aXZlIjogdHJ1ZX0='
    assert expected_data == encoded_data


def test_encode_from_str():
    """
    Validates encode_from_str with mock data.
    """
    actual_data = 'String to be encoded'
    encoded_data = encode_from_str(actual_data)
    expected_data = 'U3RyaW5nIHRvIGJlIGVuY29kZWQ='
    assert expected_data == encoded_data


def test_encode_from_bytes():
    """
    Validates encode_from_bytes with mock data.
    """
    actual_data = b'ABCDEFabcdefABCDEF'
    encoded_data = encode_from_bytes(actual_data)
    expected_data = 'QUJDREVGYWJjZGVmQUJDREVG'
    assert expected_data == encoded_data


def test_decode_to_str():
    """
    Validates decode_to_str with mock data.
    """
    actual_data = 'U3RyaW5nIHRvIGJlIGVuY29kZWQ='
    decoded_data = decode_to_str(actual_data)
    expected_data = 'String to be encoded'
    assert expected_data == decoded_data


def test_decode_to_bytes():
    """
    Validates decode_to_bytes with mock data.
    """
    actual_data = 'QUJDREVGYWJjZGVmQUJDREVG'
    decoded_data = decode_to_bytes(actual_data)
    expected_data = b'ABCDEFabcdefABCDEF'
    assert expected_data == decoded_data


def test_decode_to_dict():
    """
    Validates decode_to_dict with mock data.
    """
    actual_data = 'eyJyZXNvdXJjZVR5cGUiOiAiUGF0aWVudCIsICJpZCI6ICIwMDEiLCAiYWN0aXZlIjogdHJ1ZX0='
    decoded_data = decode_to_dict(actual_data)
    expected_data = {
        "resourceType": "Patient",
        "id": "001",
        "active": True
    }
    assert expected_data == decoded_data
