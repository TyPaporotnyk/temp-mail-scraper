import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.exception_handlers import register_exception_handlers
from app.api.routes.tempmail import router
from app.core import config
from app.core.container import ApplicationContainer
from app.core.logging import configure_logging
from app.infrastructure.browser.manager import BrowserManager, BrowserManagerSettings
from app.infrastructure.tempmail.client import TempMailClient
from app.infrastructure.tempmail.settings import TempMailClientSettings
from app.services.tempmail import TempMailService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncIterator[None]:
    browser_manager_settings = BrowserManagerSettings(
        browser_config=config.BROWSER_CONFIG,
        browser_headless=config.BROWSER_HEADLESS,
        browser_humanize=config.BROWSER_HUMANIZE,
        browser_storage_state_path=config.BROWSER_STORAGE_STATE_PATH,
        action_timeout_ms=config.ACTION_TIMEOUT_MS,
        navigation_timeout_ms=config.NAVIGATION_TIMEOUT_MS,
    )

    client_settings = TempMailClientSettings(
        tempail_url="https://tempail.com/en/",
        action_timeout_ms=30_000,
        navigation_timeout_ms=30_000,
    )

    browser_manager = BrowserManager(browser_manager_settings)
    await browser_manager.start()

    temp_mail_client = TempMailClient(
        browser_manager=browser_manager,
        settings=client_settings,
    )

    temp_mail_service = TempMailService(
        client=temp_mail_client,
    )

    app.state.container = ApplicationContainer(
        browser_manager=browser_manager,
        temp_mail_client=temp_mail_client,
        temp_mail_service=temp_mail_service,
    )

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
    register_exception_handlers(application)

    return application


app = create_app()
