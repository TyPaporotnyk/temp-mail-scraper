import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from typing import cast

from camoufox.async_api import AsyncCamoufox
from playwright.async_api import Browser, BrowserContext, Page
from playwright.async_api import Error as PlaywrightError

from app.domain.exceptions import BrowserSessionError, BrowserUnavailableError
from app.infrastructure.browser.settings import BrowserManagerSettings

logger = logging.getLogger(__name__)


class BrowserManager:
    def __init__(self, settings: BrowserManagerSettings) -> None:
        self._settings = settings

        self._camoufox: AsyncCamoufox | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

        self._lock = asyncio.Lock()

    async def start(self) -> None:
        async with self._lock:
            await self._start()

    async def stop(self) -> None:
        async with self._lock:
            await self._close()

    @asynccontextmanager
    async def page(self) -> AsyncIterator[Page]:
        async with self._lock:
            try:
                await self._ensure_ready()

                if self._page is None:
                    raise BrowserUnavailableError("Browser page is unavailable")

                yield self._page

            except PlaywrightError as exc:
                logger.warning("Playwright operation failed", exc_info=True)

                await self._restart()

                raise BrowserSessionError("Browser operation failed") from exc
            else:
                await self._save_storage_state()

    async def _start(self) -> None:
        if self._is_ready():
            return

        logger.info("Starting Playwright browser")

        try:
            self._camoufox = AsyncCamoufox(
                headless=self._settings.browser_headless,
                config=self._settings.browser_config,
                i_know_what_im_doing=True,
                humanize=True,
                os=("windows",),
            )

            browser = await self._camoufox.__aenter__()
            self._browser = cast(Browser, browser)

            storage_path = self._settings.browser_storage_state_path
            if storage_path is not None and storage_path.exists():
                logger.info(
                    "Loading browser state from %s",
                    storage_path,
                )

                self._context = await self._browser.new_context(
                    storage_state=storage_path,
                )
            else:
                self._context = await self._browser.new_context()

            self._context.set_default_timeout(self._settings.action_timeout_ms)
            self._context.set_default_navigation_timeout(self._settings.navigation_timeout_ms)

            self._page = await self._context.new_page()

            self._page.on(
                "crash",
                lambda _: logger.error("Browser page crashed"),
            )

            self._browser.on(
                "disconnected",
                lambda _: logger.warning("Firefox was disconnected"),
            )

            logger.info(
                "Browser started successfully",
            )

        except Exception as exc:
            logger.exception("Could not start Playwright browser")

            await self._close()

            raise BrowserUnavailableError("Could not start Firefox") from exc

    async def _ensure_ready(self) -> None:
        if self._is_ready():
            return

        logger.warning("Browser session is unavailable, restarting")

        await self._restart()

    def _is_ready(self) -> bool:
        if self._browser is None:
            return False

        if not self._browser.is_connected():
            return False

        if self._context is None:
            return False

        if self._page is None:
            return False

        if self._page.is_closed():
            return False

        return True

    async def _restart(self) -> None:
        logger.warning("Restarting Playwright browser")

        await self._close()
        await self._start()

    async def _save_storage_state(self) -> None:
        path = self._settings.browser_storage_state_path

        if path is None or self._context is None:
            return

        try:
            await self._context.storage_state(
                path=str(path),
                indexed_db=True,
            )
        except PlaywrightError:
            logger.warning(
                "Could not save browser storage state",
                exc_info=True,
            )

    async def _close(self) -> None:
        context = self._context
        browser = self._browser

        self._page = None
        self._context = None
        self._browser = None

        if context is not None:
            with suppress(Exception):
                await context.close()

        if browser is not None:
            with suppress(Exception):
                await browser.close()

        logger.info("Playwright browser stopped")
