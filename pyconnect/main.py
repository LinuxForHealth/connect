"""
main.py

Bootstraps the Fast API application and Uvicorn processes
"""
from fastapi import (FastAPI,
                     HTTPException)
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
import uvicorn
from pyconnect.config import get_settings
from pyconnect.routes.api import router
from pyconnect import __version__
from pyconnect.server_handlers import (close_internal_clients,
                                       configure_internal_integrations,
                                       configure_logging,
                                       http_exception_handler)
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address


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
    app.add_event_handler('startup', configure_internal_integrations)
    app.add_event_handler('shutdown', close_internal_clients)
    app.add_exception_handler(HTTPException, http_exception_handler)

    # use the slowapi rate limiter
    app.add_middleware(SlowAPIMiddleware)
    limiter = Limiter(key_func=get_remote_address, default_limits=["5/second"])
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    return app


if __name__ == '__main__':
    settings = get_settings()

    uvicorn_params = {
        'app': settings.uvicorn_app,
        'host': settings.uvicorn_host,
        'log_config': None,
        'port': settings.uvicorn_port,
        'reload': settings.uvicorn_reload,
        'ssl_keyfile': settings.pyconnect_cert_key,
        'ssl_certfile': settings.pyconnect_cert
    }

    uvicorn.run(**uvicorn_params)
