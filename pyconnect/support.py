"""
support.py

pyConnect convenience functions
"""
import socket
from typing import List


def ping_host(hostname: str, port: int) -> bool:
    """
    Pings a host and connects to confirm its availability.
    :param hostname: The hostname or ip address
    :param port: The port to connect on
    :return: True if the host is available, False if an "address info" or ConnectionError occurs
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((hostname, port))
        except (socket.gaierror, ConnectionError):
            return False
    return True


def get_host_ports(service_setting: str, delimiter: str = None) -> List[tuple]:
    """
    Parses a service setting string into a list of (hostname, port) entries
    :param service_setting: The service setting string
    :param delimiter: the optional delimiter used to separate entries oin the service setting.
    :return: List of (hostname, port) entries
    """
    def parse_service(service: str) -> tuple:
        service_tokens = service.split(':')
        host_name = service_tokens[0].strip()
        port = int(service_tokens[1]) if len(service_tokens) >= 2 else None
        return host_name, port

    host_ports = []
    if delimiter:
        services = service_setting.split(delimiter)
        host_ports = [parse_service(s) for s in services]
    else:
        host_ports.append(parse_service(service_setting))

    return host_ports


def is_service_available(service_setting: str, delimiter: str = None) -> bool:
    """
    Tests one or more services for availability using a TCP socket connection.
    The service_setting contains one or more addresses defined as [host]:[port].
    Multiple entries are supported using a delimiter. E.g [host]:[port],[host]:[port]

    :param service_setting: the address string
    :param delimiter: optional delimiter
    :return: True if all services can be reached, otherwise returns False
    """
    host_ports = get_host_ports(service_setting, delimiter=delimiter)
    test_results = [ping_host(hp[0], hp[1]) for hp in host_ports]
    return all(test_results)
