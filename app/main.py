import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import router
from app.core import config
from app.core.logging import configure_logging
from app.infrastructure.browser.manager import BrowserManager, BrowserManagerSettings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncIterator[None]:
    browser_manager_settings = BrowserManagerSettings(
        browser_config=config.BROWSER_CONFIG,
        browser_headless=config.BROWSER_HEADLESS,
        browser_storage_state_path=config.BROWSER_STORAGE_STATE_PATH,
        action_timeout_ms=config.ACTION_TIMEOUT_MS,
        navigation_timeout_ms=config.NAVIGATION_TIMEOUT_MS,
    )
    browser_manager = BrowserManager(browser_manager_settings)

    app.state.browser_manager = browser_manager

    await browser_manager.start()
    logger.info("Application started")

    try:
        yield
    finally:
        await browser_manager.stop()
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

    application.include_router(router)

    return application


app = create_app()
