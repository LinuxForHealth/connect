import logging
import logging.config
import os
import sys
import yaml
from yaml import YAMLError
from fastapi import (HTTPException,
                     Request)
from fastapi.responses import JSONResponse
from pyconnect.config import get_settings
from pyconnect.clients import (get_kafka_producer,
                               get_nats_client)
from pyconnect.support.listeners import (create_kafka_listeners,
                                         remove_kafka_listeners)
from pyconnect.support.subscribers import create_nats_subscribers


logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """
    Configures logging for the pyconnect application.
    Logging configuration is parsed from the setting/environment variable LOGGING_CONFIG_PATH, if present.
    If LOGGING_CONFIG_PATH is not found, a basic config is applied.
    """
    def apply_basic_config():
        """Applies a basic config for console logging"""
        logging.basicConfig(stream=sys.stdout,
                            level=logging.INFO,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    settings = get_settings()

    if os.path.exists(settings.logging_config_path):
        with open(settings.logging_config_path, 'r') as f:
            try:
                logging_config = yaml.safe_load(f)
                logging.config.dictConfig(logging_config)
                logger.info(f'Loaded logging configuration from {settings.logging_config_path}')
            except YAMLError as e:
                apply_basic_config()
                logger.error(f'Unable to load logging configuration from file: {e}.')
                logger.info('Applying basic logging configuration.')
    else:
        apply_basic_config()
        logger.info('Logging configuration not found. Applying basic logging configuration.')


def log_configuration() -> None:
    """
    Logs pyConnect configuration settings.
    "General" settings are logged at an INFO level.
    "Internal" settings for clients/components are logged at a DEBUG level.
    """
    settings = get_settings()
    header_footer_length = 50

    logger.info('*' * header_footer_length)
    logger.info('pyConnect Configuration Settings')
    logger.info('=' * header_footer_length)
    logger.info(f'UVICORN_APP: {settings.uvicorn_app}')
    logger.info(f'UVICORN_HOST: {settings.uvicorn_host}')
    logger.info(f'UVICORN_PORT: {settings.uvicorn_port}')
    logger.info(f'UVICORN_RELOAD: {settings.uvicorn_reload}')
    logger.info('=' * header_footer_length)

    logger.info(f'CERTIFICATE_AUTHORITY_PATH: {settings.certificate_authority_path}')
    logger.info(f'LOGGING_CONFIG_PATH: {settings.logging_config_path}')
    logger.info('=' * header_footer_length)

    logger.debug(f'KAFKA_BOOTSTRAP_SERVERS: {settings.kafka_bootstrap_servers}')
    logger.debug(f'KAFKA_PRODUCER_ACKS: {settings.kafka_producer_acks}')
    logger.debug('=' * header_footer_length)

    logger.debug(f'NATS_SERVERS: {settings.nats_servers}')
    logger.debug(f'NATS_ALLOW_RECONNECT: {settings.nats_allow_reconnect}')
    logger.debug(f'NATS_MAX_RECONNECT_ATTEMPTS: {settings.nats_max_reconnect_attempts}')
    logger.debug(f'NATS_ROOTCA_FILE: {settings.nats_rootCA_file}')
    logger.debug(f'NATS_CERT_FILE: {settings.nats_cert_file}')
    logger.debug(f'NATS_KEY_FILE: {settings.nats_key_file}')
    logger.debug('=' * header_footer_length)

    logger.debug(f'PYCONNECT_CERT: {settings.pyconnect_cert}')
    logger.debug(f'PYCONNECT_CERT_KEY: {settings.pyconnect_cert_key}')
    logger.debug('=' * header_footer_length)

    logger.info('*' * header_footer_length)


async def configure_internal_integrations() -> None:
    """
    Configure internal integrations to support:
    - Kafka
    - NATS Messaging/Jetstream
    """
    get_kafka_producer()
    await get_nats_client()
    await create_nats_subscribers()
    create_kafka_listeners()


def close_internal_clients() -> None:
    """
    Closes internal pyConnect client connections:
    - Kafka
    - NATS
    """
    kafka_producer = get_kafka_producer()
    kafka_producer.close()

    nats_client = get_nats_client()
    nats_client.close()

    remove_kafka_listeners()


async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Allows HTTPExceptions to be thrown without being parsed against a response model.
    """
    return JSONResponse(
        status_code = exc.status_code,
        content = {'detail': f'{exc.detail}'}
    )
