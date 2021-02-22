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
    kafka_producer_acks: str = 'all'

    # nats
    nats_servers: List[str] = ['tls://localhost:4222']
    nats_allow_reconnect: bool = True
    nats_max_reconnect_attempts: int = 10

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
