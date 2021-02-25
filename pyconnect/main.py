"""
main.py

Bootstraps the Fast API application and Uvicorn processes
"""
from fastapi import FastAPI
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
import uvicorn
from pyconnect.config import get_settings
from pyconnect.routes.api import router
from pyconnect import __version__
from pyconnect.server_handlers import (configure_global_clients,
                                       configure_logging)

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
    app.add_event_handler('startup', configure_logging)
    app.add_event_handler('startup', configure_global_clients)
    return app


app = get_app()

if __name__ == '__main__':
    uvicorn_params = {
        'app': settings.uvicorn_app,
        'host': settings.uvicorn_host,
        'port': settings.uvicorn_port,
        'reload': settings.uvicorn_reload,
        'ssl_keyfile': settings.pyconnect_cert_key,
        'ssl_certfile': settings.pyconnect_cert
    }

    uvicorn.run(**uvicorn_params)
