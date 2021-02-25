import logging.config
import os
import sys
import yaml
from yaml import YAMLError
from pyconnect.config import get_settings
from pyconnect.clients import (get_kafka_producer,
                               get_nats_client)


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
            except YAMLError as e:
                apply_basic_config()
                logging.error(f'Unable to load logging configuration from file: {e}.')
                logging.info('Applying basic logging configuration.')
    else:
        apply_basic_config()
        logging.info('Logging configuration not found. Applying basic logging configuration.')


async def configure_global_clients() -> None:
    """
    Configures pyConnect service clients for internal and external integrations
    """
    get_kafka_producer()
    await get_nats_client()
