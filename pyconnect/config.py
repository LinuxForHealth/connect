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


class Settings(BaseSettings):
    """
    pyconnect application settings
    """
    # kakfa
    kafka_bootstrap_servers: str = 'localhost:9094'

    # logging
    logging_config_path: str = 'logging.yaml'

    # uvicorn settings
    uvicorn_cert: str
    uvicorn_cert_key: str
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
