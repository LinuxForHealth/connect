"""
main.py

Bootstraps the Fast API application and Uvicorn processes
"""
from fastapi import FastAPI
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from pyconnect.config import get_settings
from pyconnect.routes import status
import uvicorn


def get_app() -> FastAPI:
    """
    Creates the Fast API application instance
    :return: The application instance
    """
    app = FastAPI()
    app.add_middleware(HTTPSRedirectMiddleware)
    app.include_router(status.router, prefix='/status')
    return app


app = get_app()

if __name__ == '__main__':
    settings = get_settings()

    uvicorn_params = {
        'app': settings.uvicorn_app,
        'host': settings.uvicorn_host,
        'port': settings.uvicorn_port,
        'reload': settings.uvicorn_reload,
        'ssl_keyfile': settings.uvicorn_cert_key,
        'ssl_certfile': settings.uvicorn_cert
    }

    uvicorn.run(**uvicorn_params)
