"""
main.py

Bootstraps the Fast API application and Uvicorn processes
"""
from fastapi import (FastAPI,
                     HTTPException,
                     Request)
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging.config
import os
import yaml
import sys
from yaml.error import YAMLError
from pyconnect.config import get_settings
from pyconnect.routes.api import router
from pyconnect import __version__

settings = get_settings()


def get_app() -> FastAPI:
    """
    Creates the Fast API application instance
    :return: The application instance
    """
    app = FastAPI(
        title='LinuxForHealth pyConnect',
        description='LinuxForHealth Connectors for Inbound Data Processing',
        version=__version__,
    )
    app.add_middleware(HTTPSRedirectMiddleware)
    app.include_router(router)
    return app


app = get_app()

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code = exc.status_code,
        content = {"detail": f"{exc.detail}"}
    )

@app.on_event('startup')
def configure_logging():
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


if __name__ == '__main__':
    uvicorn_params = {
        'app': settings.uvicorn_app,
        'host': settings.uvicorn_host,
        'port': settings.uvicorn_port,
        'reload': settings.uvicorn_reload,
        'ssl_keyfile': settings.uvicorn_cert_key,
        'ssl_certfile': settings.uvicorn_cert
    }

    uvicorn.run(**uvicorn_params)
