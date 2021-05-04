import logging
import logging.config
import os
import sys
import yaml
from yaml import YAMLError
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from connect.config import get_settings
from connect.clients.kafka import (
    get_kafka_producer,
    create_kafka_listeners,
    stop_kafka_listeners,
)
from connect.clients.nats import (
    create_nats_subscribers,
    get_nats_client,
    stop_nats_clients,
)


logger = logging.getLogger(__name__)


def add_trace_logging():
    """
    Adds trace level logging support to logging and the root logging class
    """

    def trace(self, message, *args, **kwargs):
        """
        Generates a TRACE log record
        """
        self.log(5, message, *args, **kwargs)

    logging.addLevelName(5, "TRACE")
    logging.getLoggerClass().trace = trace


def configure_logging() -> None:
    """
    Configures logging for the connect application.
    Logging configuration is parsed from the setting/environment variable LOGGING_CONFIG_PATH, if present.
    If LOGGING_CONFIG_PATH is not found, a basic config is applied.
    """

    def apply_basic_config():
        """Applies a basic config for console logging"""
        add_trace_logging()
        logging.basicConfig(
            stream=sys.stdout,
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    settings = get_settings()

    if os.path.exists(settings.connect_logging_config_path):
        with open(settings.connect_logging_config_path, "r") as f:
            try:
                logging_config = yaml.safe_load(f)
                logging.config.dictConfig(logging_config)
                logger.info(
                    f"Loaded logging configuration from {settings.connect_logging_config_path}"
                )
                add_trace_logging()
            except YAMLError as e:
                apply_basic_config()
                logger.error(f"Unable to load logging configuration from file: {e}.")
                logger.info("Applying basic logging configuration.")
    else:
        apply_basic_config()
        logger.info(
            "Logging configuration not found. Applying basic logging configuration."
        )


def log_configuration() -> None:
    """
    Logs Connect configuration settings.
    "General" settings are logged at an INFO level.
    "Internal" settings for clients/components are logged at a DEBUG level.
    """
    settings = get_settings()
    header_footer_length = 50

    logger.info("*" * header_footer_length)
    logger.info("Connect Configuration Settings")
    logger.info("=" * header_footer_length)
    logger.info(f"UVICORN_APP: {settings.uvicorn_app}")
    logger.info(f"UVICORN_HOST: {settings.uvicorn_host}")
    logger.info(f"UVICORN_PORT: {settings.uvicorn_port}")
    logger.info(f"UVICORN_RELOAD: {settings.uvicorn_reload}")
    logger.info("=" * header_footer_length)

    logger.info(f"CERTIFICATE_AUTHORITY_PATH: {settings.certificate_authority_path}")
    logger.info(f"LOGGING_CONFIG_PATH: {settings.connect_logging_config_path}")
    logger.info("=" * header_footer_length)

    logger.debug(f"CONNECT_CERT_DIRECTORY: {settings.connect_cert_directory}")
    logger.debug(f"CONNECT_CONFIG_DIRECTORY: {settings.connect_config_directory}")
    logger.debug(f"CONNECT_CERT: {settings.connect_cert_name}")
    logger.debug(f"CONNECT_CERT_KEY: {settings.connect_cert_key_name}")
    logger.debug("=" * header_footer_length)

    logger.debug(f"KAFKA_BOOTSTRAP_SERVERS: {settings.kafka_bootstrap_servers}")
    logger.debug(f"KAFKA_PRODUCER_ACKS: {settings.kafka_producer_acks}")
    logger.debug("=" * header_footer_length)

    logger.debug(f"NATS_SERVERS: {settings.nats_servers}")
    logger.debug(f"NATS_ALLOW_RECONNECT: {settings.nats_allow_reconnect}")
    logger.debug(f"NATS_MAX_RECONNECT_ATTEMPTS: {settings.nats_max_reconnect_attempts}")
    logger.debug("=" * header_footer_length)

    logger.info("*" * header_footer_length)


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


async def close_internal_clients() -> None:
    """
    Closes internal Connect client connections:
    - Kafka
    - NATS
    """
    kafka_producer = get_kafka_producer()
    kafka_producer.close()

    await stop_nats_clients()
    stop_kafka_listeners()


async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Allows HTTPExceptions to be thrown without being parsed against a response model.
    """
    return JSONResponse(
        status_code=exc.status_code, content={"detail": f"{exc.detail}"}
    )
