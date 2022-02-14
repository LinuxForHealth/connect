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
import certifi
import socket
import ssl

host_name = socket.gethostname()
nats_timing_subject = "EVENTS.timing"
nats_timing_consumer = "timing.EVENTS"
nats_sync_subject = "EVENTS.sync"
nats_sync_consumer = "sync.EVENTS"
nats_retransmit_subject = "EVENTS.retransmit"
nats_retransmit_consumer = "retransmit.EVENTS"
nats_app_sync_subject = "EVENTS.app_sync"
nats_app_sync_consumer = "app_sync.EVENTS"
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
    # external FHIR server URLs or []
    # Example: ["https://fhiruser:change-password@localhost:9443/fhir-server/api/v4"]
    connect_external_fhir_servers: List[str] = []
    connect_generate_fhir_server_url: bool = True
    connect_rate_limit: str = "10000/second"
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
    kafka_poll_timeout: float = 10.0
    kafka_topics_timeout: float = 0.5

    # nats
    nats_servers: List[str] = ["tls://nats-server:4222"]
    nats_sync_subscribers: List[str] = []
    nats_allow_reconnect: bool = True
    nats_max_reconnect_attempts: int = 10
    nats_nk_file: str = "nats-server.nk"
    nats_enable_retransmit: bool = True
    nats_retransmit_loop_interval_secs: int = 10
    nats_retransmit_max_retries: int = 20

    # ipfs-cluster
    ipfs_cluster_uri: str = "http://0.0.0.0:9099"
    ipfs_http_uri: str = "http://127.0.0.1:5001"
    # -1 replication factor replicates to all nodes in the cluster, or set to desired # of replicas
    ipfs_cluster_replication_factor: int = -1

    # OpenSearch
    opensearch_server: str = "localhost"
    opensearch_port: int = 9200
    opensearch_user: str = "user"
    opensearch_password: str = "password"

    class Config:
        case_sensitive = False


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
