"""
test_encoding_utils.py

Tests Connect support base64 encoding convenience functions
"""
from connect.support.encoding import (
    encode_from_dict,
    encode_from_str,
    encode_from_bytes,
    decode_to_str,
    decode_to_bytes,
    decode_to_dict,
    ConnectEncoder,
)
import pytest
import datetime
import uuid
import copy
import decimal


@pytest.fixture(scope="module")
def dictionary_data():
    """
    Dictionary data fixture used for encoding/decoding tests.
    """
    return {
        "resourceType": "Patient",
        "id": "001",
        "id01": 100,
        "id02": 900.123,
        "active": True,
        "start_date": datetime.date(2021, 3, 23),
        "start_date_time": datetime.datetime(
            2021, 3, 23, hour=15, minute=10, second=12
        ),
        "uuid": uuid.UUID("d897987e-133b-4236-996d-554c012ee8d9"),
        "location": {
            "lat": decimal.Decimal("37.421925"),
            "long": decimal.Decimal("-122.0841293"),
        },
    }


@pytest.fixture(scope="module")
def decoded_dictionary_data(dictionary_data):
    """
    Represents the "decoded" version of the dictionary data that has been encoded and then decoded.
    date, datetime, time, and uuid objects are decoded as string representations
    """
    copied_dictionary = copy.deepcopy(dictionary_data)
    copied_dictionary["start_date"] = copied_dictionary["start_date"].isoformat()
    copied_dictionary["start_date_time"] = copied_dictionary[
        "start_date_time"
    ].isoformat()
    copied_dictionary["uuid"] = str(copied_dictionary["uuid"])
    copied_dictionary["location"]["lat"] = float(copied_dictionary["location"]["lat"])
    copied_dictionary["location"]["long"] = float(copied_dictionary["location"]["long"])
    return copied_dictionary


@pytest.fixture(scope="module")
def encoded_dictionary_data():
    """
    The encoded representation of the dictionary data fixture.
    """
    return '{"resourceType": "Patient", "id": "001", "id01": 100, "id02": 900.123, "active": true, "start_date": "2021-03-23", "start_date_time": "2021-03-23T15:10:12", "uuid": "d897987e-133b-4236-996d-554c012ee8d9", "location": {"lat": 37.421925, "long": -122.0841293}}'


def test_encode_from_dict(dictionary_data):
    """
    Validates encode_from_dict with mock data.
    :param dictionary_data: The dictionary data fixture used as the encoding input.
    """
    encoded_data = encode_from_dict(dictionary_data)
    expected_data = "eyJyZXNvdXJjZVR5cGUiOiAiUGF0aWVudCIsICJpZCI6ICIwMDEiLCAiaWQwMSI6IDEwMCwgImlkMDIiOiA5MDAuMTIzLCAiYWN0aXZlIjogdHJ1ZSwgInN0YXJ0X2RhdGUiOiAiMjAyMS0wMy0yMyIsICJzdGFydF9kYXRlX3RpbWUiOiAiMjAyMS0wMy0yM1QxNToxMDoxMiIsICJ1dWlkIjogImQ4OTc5ODdlLTEzM2ItNDIzNi05OTZkLTU1NGMwMTJlZThkOSIsICJsb2NhdGlvbiI6IHsibGF0IjogMzcuNDIxOTI1LCAibG9uZyI6IC0xMjIuMDg0MTI5M319"
    assert expected_data == encoded_data


def test_encode_from_str():
    """
    Validates encode_from_str with mock data.
    """
    actual_data = "String to be encoded"
    encoded_data = encode_from_str(actual_data)
    expected_data = "U3RyaW5nIHRvIGJlIGVuY29kZWQ="
    assert expected_data == encoded_data


def test_encode_from_bytes():
    """
    Validates encode_from_bytes with mock data.
    """
    actual_data = b"ABCDEFabcdefABCDEF"
    encoded_data = encode_from_bytes(actual_data)
    expected_data = "QUJDREVGYWJjZGVmQUJDREVG"
    assert expected_data == encoded_data


def test_decode_to_str():
    """
    Validates decode_to_str with mock data.
    """
    actual_data = "U3RyaW5nIHRvIGJlIGVuY29kZWQ="
    decoded_data = decode_to_str(actual_data)
    expected_data = "String to be encoded"
    assert expected_data == decoded_data


def test_decode_to_bytes():
    """
    Validates decode_to_bytes with mock data.
    """
    actual_data = "QUJDREVGYWJjZGVmQUJDREVG"
    decoded_data = decode_to_bytes(actual_data)
    expected_data = b"ABCDEFabcdefABCDEF"
    assert expected_data == decoded_data


def test_decode_to_dict(decoded_dictionary_data):
    """
    Validates decode_to_dict with mock data.
    :param: decoded_dictionary_data: The decoded dictionary fixture used as the "expected result"
    """
    actual_data = "eyJyZXNvdXJjZVR5cGUiOiAiUGF0aWVudCIsICJpZCI6ICIwMDEiLCAiaWQwMSI6IDEwMCwgImlkMDIiOiA5MDAuMTIzLCAiYWN0aXZlIjogdHJ1ZSwgInN0YXJ0X2RhdGUiOiAiMjAyMS0wMy0yMyIsICJzdGFydF9kYXRlX3RpbWUiOiAiMjAyMS0wMy0yM1QxNToxMDoxMiIsICJ1dWlkIjogImQ4OTc5ODdlLTEzM2ItNDIzNi05OTZkLTU1NGMwMTJlZThkOSIsICJsb2NhdGlvbiI6IHsibGF0IjogMzcuNDIxOTI1LCAibG9uZyI6IC0xMjIuMDg0MTI5M319"
    decoded_data = decode_to_dict(actual_data)
    assert decoded_dictionary_data == decoded_data


def test_connect_encoder(dictionary_data, encoded_dictionary_data):
    """
    Tests the custom connect encoder
    :param dictionary_data: The fixture used as the encoding input
    :param encoded_dictionary_data: The fixture used as the expected encoding result
    """
    encoder = ConnectEncoder()
    actual_value = encoder.encode(dictionary_data)
    assert encoded_dictionary_data == actual_value
