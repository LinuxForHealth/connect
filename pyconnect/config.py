"""
config.py

Contains application settings encapsulated using Pydantic BaseSettings.
Settings may be overriden using environment variables.
Example:
    override uvicorn_port default setting
    export UVICORN_PORT=5050
    or
    UVICORN_PORT=5050 python pyconnect/main.py
"""
from pydantic import BaseSettings
from functools import lru_cache
from pathlib import Path
from typing import List
from datetime import timedelta
import os
import certifi
import socket

host_name = socket.gethostname()
nats_sync_subject = 'EVENTS.sync'
kafka_sync_topic = 'LFH_SYNC'


class Settings(BaseSettings):
    """
    pyconnect application settings
    """

    # First preference to a defined env var 'LOCAL_CERTS_PATH'
    application_cert_path: str = os.getenv('APPLICATION_CERT_PATH',
                                           os.path.join(Path(__file__).parents[1], 'local-certs'))

    # general certificate settings
    # path to "standard" CA certificates
    certificate_authority_path: str = certifi.where()
    certificate_verify: bool = False

    # kakfa
    kafka_bootstrap_servers: List[str] = ['localhost:9094']
    kafka_segments_purge_timeout: float = timedelta(minutes=10).total_seconds()
    kafka_message_chunk_size: int = 900*1024  # 900 KB chunk_size
    kafka_producer_acks: str = 'all'
    kafka_consumer_default_group_id: str = 'lfh_consumer_group'
    kafka_consumer_default_enable_auto_commit: bool = False
    kafka_consumer_default_enable_auto_offset_store: bool = False
    kafka_consumer_default_poll_timeout_secs: float = 1.0
    kafka_consumer_default_auto_offset_reset: str = 'error'
    kafka_admin_new_topic_partitions: int = 1
    kafka_admin_new_topic_replication_factor: int = 1

    # nats
    nats_servers: List[str] = ['tls://localhost:4222']
    nats_allow_reconnect: bool = True
    nats_max_reconnect_attempts: int = 10
    nats_rootCA_file: str = application_cert_path + '/rootCA.pem'
    nats_cert_file: str = application_cert_path + '/nats-server.pem'
    nats_key_file: str = application_cert_path + '/nats-server.key'

    # pyConnect
    pyconnect_cert: str = application_cert_path + '/lfh.pem'
    pyconnect_cert_key: str = application_cert_path + '/lfh.key'
    lfh_id: str = host_name

    # logging
    logging_config_path: str = 'logging.yaml'

    # uvicorn settings
    uvicorn_app: str = 'pyconnect.asgi:app'
    uvicorn_host: str = '0.0.0.0'
    uvicorn_port: int = 5000
    uvicorn_reload: bool = False

    # external FHIR server URL or None
    # Example: 'https://fhiruser:change-password@localhost:9443/fhir-server/api/v4'
    fhir_r4_externalserver: str = None

    class Config:
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Returns the settings instance"""
    return Settings()
