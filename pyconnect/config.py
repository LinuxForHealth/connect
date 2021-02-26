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
import os
import certifi

local_certs_path = os.path.join(Path(__file__).parents[1], 'local-certs')


class Settings(BaseSettings):
    """
    pyconnect application settings
    """
    # general certificate settings
    # path to "standard" CA certificates
    certificate_authority_path: str = certifi.where()

    # kakfa
    kafka_bootstrap_servers: List[str] = ['localhost:9094']
    kafka_segments_purge_timeout: int = 600   # 10 minutes in seconds {10 * 60}
    kafka_message_chunk_size: int = 900*1024  # 900 KB chunk_size
    kafka_producer_acks: str = 'all'
    kafka_consumer_default_group_id: str = 'lfh_consumer_group'
    kafka_consumer_default_concurrent_listeners: int = 3
    kafka_consumer_monitor_freq_in_secs: int = 3

    # nats
    nats_servers: List[str] = ['tls://localhost:4222']
    nats_allow_reconnect: bool = True
    nats_max_reconnect_attempts: int = 10
    nats_rootCA_file: str = local_certs_path + '/rootCA.pem'
    nats_cert_file: str = local_certs_path + '/nats-server.pem'
    nats_key_file: str = local_certs_path + '/nats-server.key'

    # pyConnect
    pyconnect_cert: str
    pyconnect_cert_key: str

    # logging
    logging_config_path: str = 'logging.yaml'

    # uvicorn settings
    uvicorn_app: str = 'pyconnect.main:app'
    uvicorn_host: str = '0.0.0.0'
    uvicorn_port: int = 5000
    uvicorn_reload: bool = False

    class Config:
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Returns the settings instance"""
    return Settings()
