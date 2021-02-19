"""
test_support.py

Tests pyConnect support/convenience functions
"""
import socket
from pyconnect.support import ping_host, get_host_ports


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
    service_setting = 'localhost:9090'
    expected = [('localhost', 9090)]
    actual = get_host_ports(service_setting)
    assert expected == actual

    service_setting = 'localhost'
    expected = [('localhost', None)]
    actual = get_host_ports(service_setting)
    assert expected == actual

    service_setting = 'localhost:9090, localhost:9091'
    actual = get_host_ports(service_setting, delimiter=',')
    expected = [('localhost', 9090), ('localhost', 9091)]
    assert expected == actual

    service_setting = 'localhost:9090,localhost:9091'
    actual = get_host_ports(service_setting, delimiter=',')
    expected = [('localhost', 9090), ('localhost', 9091)]
    assert expected == actual