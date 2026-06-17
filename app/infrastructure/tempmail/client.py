import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from playwright.async_api import Page

from app.domain.exceptions import EmailNotFoundError, ScrapingError
from app.domain.models import EmailMessage, InboxMessage
from app.infrastructure.browser.manager import BrowserManager
from app.infrastructure.tempmail.page_service import (
    InboxSnapshot,
    MessageReference,
    TempMailPageService,
)
from app.infrastructure.tempmail.selectors import (
    SELECTORS,
    TempMailSelectors,
)
from app.infrastructure.tempmail.settings import TempMailClientSettings

logger = logging.getLogger(__name__)


class TempMailClient:
    def __init__(
        self,
        browser_manager: BrowserManager,
        settings: TempMailClientSettings,
        selectors: TempMailSelectors = SELECTORS,
    ) -> None:
        self._browser_manager = browser_manager
        self._page_service = TempMailPageService(settings=settings, selectors=selectors)

        self._message_refs: dict[str, MessageReference] = {}
        self._browser_generation = browser_manager.generation

    async def get_current_email(self) -> str:
        async with self._page_session() as page:
            await self._page_service.open_home(page)
            return await self._page_service.read_current_email(page)

    async def list_messages(self) -> list[InboxMessage]:
        async with self._page_session() as page:
            snapshot = await self._load_inbox(page)
            return snapshot.messages

    async def get_message(self, message_id: str) -> EmailMessage:
        normalized_id = self._normalize_message_id(message_id)

        async with self._page_session() as page:
            reference = await self._get_message_reference(
                page=page,
                message_id=normalized_id,
            )
            return await self._page_service.get_message(page, reference)

    async def refresh_email(self) -> str:
        async with self._page_session() as page:
            previous_email, current_email = await self._page_service.refresh_email(page)

            self._message_refs.clear()

            logger.info(
                "Temporary email refreshed, old=%s new=%s",
                self._mask_email(previous_email),
                self._mask_email(current_email),
            )

            return current_email

    @asynccontextmanager
    async def _page_session(self) -> AsyncIterator[Page]:
        async with self._browser_manager.page() as page:
            self._synchronize_generation()
            yield page

    async def _load_inbox(self, page: Page) -> InboxSnapshot:
        snapshot = await self._page_service.load_inbox(page)
        self._message_refs = snapshot.references
        return snapshot

    async def _get_message_reference(self, page: Page, message_id: str) -> MessageReference:
        reference = self._message_refs.get(message_id)

        if reference is None:
            snapshot = await self._load_inbox(page)
            reference = snapshot.references.get(message_id)

        if reference is None:
            raise EmailNotFoundError(f"Email with id '{message_id}' was not found")

        return reference

    def _synchronize_generation(self) -> None:
        current_generation = self._browser_manager.generation

        if current_generation == self._browser_generation:
            return

        logger.info(
            "Browser generation changed, old=%s new=%s",
            self._browser_generation,
            current_generation,
        )

        self._message_refs.clear()
        self._browser_generation = current_generation

    @staticmethod
    def _normalize_message_id(raw_id: str) -> str:
        message_id = raw_id.strip()

        if message_id.startswith("mail_"):
            message_id = message_id.removeprefix("mail_")

        if not message_id:
            raise ScrapingError("Email has an empty id")

        return message_id

    @staticmethod
    def _mask_email(email: str) -> str:
        local_part, separator, domain = email.partition("@")

        if not separator:
            return "***"

        if len(local_part) <= 2:
            masked_local_part = "*" * len(local_part)
        else:
            masked_local_part = f"{local_part[0]}***{local_part[-1]}"

        return f"{masked_local_part}@{domain}"
