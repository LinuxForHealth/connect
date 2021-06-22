"""
config.py

Contains application settings encapsulated using Pydantic BaseSettings.
Settings may be overriden using environment variables.
Example:
    override uvicorn_port default setting
    export UVICORN_PORT=5050
    or
    UVICORN_PORT=5050 python connect/main.py
"""
from pydantic import BaseSettings
from functools import lru_cache
from typing import List
from datetime import timedelta
import os
from os.path import dirname, abspath
import certifi
import socket
import ssl

host_name = socket.gethostname()
nats_sync_subject = "EVENTS.sync"
kafka_sync_topic = "LFH_SYNC"


class Settings(BaseSettings):
    """
    connect application settings
    """

    # uvicorn settings
    uvicorn_app: str = "connect.asgi:app"
    uvicorn_host: str = "0.0.0.0"
    uvicorn_port: int = 5000
    uvicorn_reload: bool = False

    # general certificate settings
    # path to "standard" CA certificates
    certificate_authority_path: str = certifi.where()
    certificate_verify: bool = False

    # Connect
    connect_ca_file: str = certifi.where()
    connect_ca_path: str = None
    connect_cert_name: str = "lfh-connect.pem"
    connect_cert_key_name: str = "lfh-connect.key"
    connect_config_directory: str = "/home/lfh/connect/config"
    connect_lfh_id: str = host_name
    connect_logging_config_path: str = "logging.yaml"
    # external FHIR server URL or None
    # Example: 'https://fhiruser:change-password@localhost:9443/fhir-server/api/v4'
    connect_external_fhir_server: str = None
    connect_enable_rate_limit: bool = True
    connect_rate_limit: str = "5/second"
    connect_timing_enabled: bool = False

    # kakfa
    kafka_bootstrap_servers: List[str] = ["kafka:9092"]
    kafka_segments_purge_timeout: float = timedelta(minutes=10).total_seconds()
    kafka_message_chunk_size: int = 900 * 1024  # 900 KB chunk_size
    kafka_producer_acks: str = "all"
    kafka_consumer_default_group_id: str = "lfh_consumer_group"
    kafka_consumer_default_enable_auto_commit: bool = False
    kafka_consumer_default_enable_auto_offset_store: bool = False
    kafka_consumer_default_poll_timeout_secs: float = 1.0
    kafka_consumer_default_auto_offset_reset: str = "error"
    kafka_admin_new_topic_partitions: int = 1
    kafka_admin_new_topic_replication_factor: int = 1
    kafka_listener_timeout: float = 1.0
    kafka_topics_timeout: float = 0.5

    nats_servers: List[str] = ["tls://nats-server:4222"]
    nats_sync_subscribers: List[str] = []
    nats_allow_reconnect: bool = True
    nats_max_reconnect_attempts: int = 10
    nats_nk_file: str = "nats-server.nk"

    class Config:
        case_sensitive = False
        env_file = os.path.join(dirname(dirname(abspath(__file__))), ".env")


@lru_cache()
def get_settings() -> Settings:
    """Returns the settings instance"""
    return Settings()


@lru_cache()
def get_ssl_context(ssl_purpose: ssl.Purpose) -> ssl.SSLContext:
    """
    Returns a SSL Context configured for server auth with the connect certificate path
    :param ssl_purpose:
    """
    settings = get_settings()
    ssl_context = ssl.create_default_context(ssl_purpose)
    ssl_context.load_verify_locations(
        cafile=settings.connect_ca_file, capath=settings.connect_ca_path
    )
    return ssl_context
