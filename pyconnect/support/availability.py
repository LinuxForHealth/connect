"""
availability.py

 pyConnect convenience functions for verifying host/service availability
  and fetching host:port lookups
"""

from typing import List
from urllib.parse import urlsplit
import asyncio
from asyncio import StreamWriter
import logging


logger = logging.getLogger(__name__)


async def ping_host(hostname: str, port: int) -> bool:
    """
    Pings a host and connects to confirm its availability.
    :param hostname: The hostname or ip address
    :param port: The port to connect on
    :return: True if the host is available, False if an "address info" or ConnectionError occurs
    """
    writer: StreamWriter = None
    try :
        _, writer = await asyncio.open_connection(hostname, port)
    except Exception as ex:
        logger.error(f'error connecting to {hostname}:{port}')
        logger.exception(ex)
        return False
    else:
        return True
    finally:
        if writer is not None:
            await writer.close()


def get_host_ports(service_setting: List[str]) -> List[tuple]:
    """
    Parses a service setting string into a list of (hostname, port) entries
    :param service_setting: The service setting string
    :return: List of (hostname, port) entries
    """
    host_ports = []

    for service in service_setting:
        parsed_url = urlsplit(service)
        # parse a second time if hostname isn't found
        # useful for settings without a protocol scheme
        if parsed_url.hostname is None:
            parsed_url = urlsplit('//' + service)
        host_ports.append((parsed_url.hostname.strip(), parsed_url.port))
    return host_ports


async def is_service_available(service_setting: List[str]) -> bool:
    """
    Tests one or more services for availability using a TCP socket connection.
    The service_setting contains one or more addresses defined as [host]:[port].

    :param service_setting: the address string
    :return: True if all services can be reached, otherwise returns False
    """
    host_ports = get_host_ports(service_setting)
    test_results = [await ping_host(hp[0], hp[1]) for hp in host_ports]
    return all(test_results)
