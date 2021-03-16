"""
test_availability.py

Tests pyConnect service/host availability functions
"""
import asyncio
from unittest.mock import AsyncMock
import pytest
from pyconnect.support.availability import (get_host_ports,
                                            is_service_available,
                                            ping_host)


@pytest.mark.asyncio
def test_ping_host(monkeypatch):
    """
    Validates positive and negative results for ping_host.
    The underlying function used to "ping" the host, asyncio.open_connection,
    is mocked for the positive and negative test cases.
    :param monkeypatch:
    """
    with monkeypatch.context() as m:
        mock = AsyncMock(return_value=(AsyncMock(), AsyncMock()))
        m.setattr(asyncio, 'open_connection', mock)
        actual_result = asyncio.run(ping_host('some-server', 8080))
        assert actual_result is True

        mock = AsyncMock(side_effect=OSError)
        m.setattr(asyncio, 'open_connection', mock)
        actual_result = asyncio.run(ping_host('some-server', 8080))
        assert actual_result is False


def test_get_host_ports():
    """
    Validates that host and port data is parsed from settings
    """
    service_setting = ['localhost:9090']
    expected = [('localhost', 9090)]
    actual = get_host_ports(service_setting)
    assert actual == expected

    service_setting = ['localhost']
    expected = [('localhost', None)]
    actual = get_host_ports(service_setting)
    assert actual == expected

    service_setting = ['localhost:9090', 'localhost:9091']
    actual = get_host_ports(service_setting)
    expected = [('localhost', 9090), ('localhost', 9091)]
    assert actual == expected

    service_setting = ['localhost:9090', 'localhost:9091']
    actual = get_host_ports(service_setting)
    expected = [('localhost', 9090), ('localhost', 9091)]
    assert actual == expected


@pytest.mark.asyncio
def test_is_service_available(monkeypatch):
    """
    Validates that is_service_available returns True for valid connections, False when an error occurs.
    The underlying function used to confirm availability, asyncio.open_connection,
    is mocked for the positive and negative test cases.
    """
    with monkeypatch.context() as m:

        mock = AsyncMock(return_value=(AsyncMock(), AsyncMock()))
        m.setattr(asyncio, 'open_connection', mock)
        service_setting = ['https://localhost:8080', 'tls://otherhost:8080']
        actual_result = asyncio.run(is_service_available(service_setting))
        assert actual_result is True

        mock = AsyncMock(side_effect=OSError)
        m.setattr(asyncio, 'open_connection', mock)
        service_setting = ['https://localhost:9090', 'tls://otherhost:8080']
        actual_result = asyncio.run(is_service_available(service_setting))
        assert actual_result is False
