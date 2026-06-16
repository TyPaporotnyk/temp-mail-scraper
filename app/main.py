import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core import config
from app.core.logging import configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncIterator[None]:
    logger.info("Application started")

    try:
        yield
    finally:
        logger.info("Application stopped")


def create_app() -> FastAPI:
    configure_logging(config.LOG_LEVEL)

    swagger_ui_parameters = {
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "tryItOutEnabled": True,
    }

    application = FastAPI(
        title=config.APP_NAME,
        version=config.APP_VERSION,
        docs_url=config.APP_DOCS_URL,
        swagger_ui_parameters=swagger_ui_parameters,
        lifespan=lifespan,
    )

    return application


app = create_app()
