"""
test_support.py

Tests pyConnect support/convenience functions
"""
import socket
from pyconnect.support import (get_host_ports,
                               is_service_available,
                               ping_host)


def test_ping_host(monkeypatch, mock_client_socket):
    """
    Validates ping_host with a mock client socket connection.
    The mock client socket fixture returns a positive result for port 8080
    :param monkeypatch: Monkeypatch instance used for mocking
    :param mock_client_socket: A mock client socket fixture
    """
    with monkeypatch.context() as m:
        m.setattr(socket, 'socket', mock_client_socket)
        assert ping_host('some-server', 8080) is True
        assert ping_host('some-server', 8090) is False


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

    service_setting = ['localhost:9090',' localhost:9091']
    actual = get_host_ports(service_setting)
    expected = [('localhost', 9090), ('localhost', 9091)]
    assert actual == expected


def test_is_service_available(monkeypatch, mock_client_socket):
    """
    Validates that is_service_available returns True for valid connections.
    The mock client socket fixture returns a positive result for port 8080
    :param monkeypatch: Monkeypatch instance used for mocking
    :param mock_client_socket: A mock client socket fixture
    """
    with monkeypatch.context() as m:
        m.setattr(socket, 'socket', mock_client_socket)
        service_setting = ['https://localhost:8080', 'tls://otherhost:8080']
        assert is_service_available(service_setting) is True

        service_setting = ['https://localhost:9090', 'tls://otherhost:8080']
        assert is_service_available(service_setting) is False
