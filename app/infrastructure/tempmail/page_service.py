import logging
import re
from dataclasses import dataclass

from playwright.async_api import (
    Locator,
    Page,
)
from playwright.async_api import (
    TimeoutError as PlaywrightTimeoutError,
)

from app.domain.exceptions import (
    AntiBotChallengeError,
    ElementNotFoundError,
    PageLoadTimeoutError,
    ScrapingError,
)
from app.domain.models import EmailMessage, InboxMessage
from app.infrastructure.tempmail.selectors import (
    SELECTORS,
    TempMailSelectors,
)
from app.infrastructure.tempmail.settings import TempMailClientSettings

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class MessageReference:
    id: str
    href: str
    sender: str
    received_at: str


@dataclass(slots=True, frozen=True)
class InboxSnapshot:
    messages: list[InboxMessage]
    references: dict[str, MessageReference]


class TempMailPageService:
    def __init__(
        self,
        settings: TempMailClientSettings,
        selectors: TempMailSelectors = SELECTORS,
    ) -> None:
        self._settings = settings
        self._selectors = selectors

    async def open_home(self, page: Page) -> None:
        email_input = page.locator(self._selectors.email_input)

        if page.url != "about:blank" and await email_input.count() > 0:
            await self._raise_if_anti_bot(page)
            await self._accept_cookies(page)
            return

        try:
            await page.goto(
                self._settings.tempail_url,
                wait_until="domcontentloaded",
                timeout=self._settings.navigation_timeout_ms,
            )
        except PlaywrightTimeoutError as exc:
            raise PageLoadTimeoutError("Tempail page loading timed out") from exc

        await self._raise_if_anti_bot(page)
        await self._wait_visible(
            page.locator(self._selectors.email_input),
            "temporary email input",
        )
        await self._accept_cookies(page)

    async def read_current_email(self, page: Page) -> str:
        email_input = page.locator(self._selectors.email_input)

        await self._wait_visible(email_input, "temporary email input")

        email = (await email_input.input_value()).strip()

        if not email:
            raise ScrapingError("Temporary email input is empty")

        if not self._is_valid_email(email):
            raise ScrapingError("Temporary email has an invalid format")

        return email

    async def load_inbox(self, page: Page) -> InboxSnapshot:
        await self.open_home(page)
        await self._wait_for_inbox_state(page)
        return await self.read_inbox(page)

    async def read_inbox(self, page: Page) -> InboxSnapshot:
        inbox = page.locator(self._selectors.inbox_container)

        await self._wait_visible(inbox, "inbox container")

        if await self._is_inbox_empty(page):
            return InboxSnapshot(messages=[], references={})

        rows = page.locator(self._selectors.inbox_rows)
        rows_count = await rows.count()

        if rows_count == 0:
            return InboxSnapshot(messages=[], references={})

        messages: list[InboxMessage] = []
        references: dict[str, MessageReference] = {}

        for index in range(rows_count):
            row = rows.nth(index)
            reference = await self._parse_inbox_row(row=row, index=index)

            references[reference.id] = reference
            messages.append(
                InboxMessage(
                    id=reference.id,
                    sender=reference.sender,
                    received_at=reference.received_at,
                )
            )

        logger.info("Inbox parsed, messages_count=%s", len(messages))
        return InboxSnapshot(messages=messages, references=references)

    async def get_message(self, page: Page, reference: MessageReference) -> EmailMessage:
        await self._open_message(page=page, reference=reference)
        return await self._read_opened_message(page=page, reference=reference)

    async def refresh_email(self, page: Page) -> tuple[str, str]:
        await self.open_home(page)

        refresh_button = page.locator(self._selectors.refresh_button)
        previous_email = await self.read_current_email(page)

        await self._wait_visible(refresh_button, "refresh email button")
        await refresh_button.click()

        try:
            await page.wait_for_function(
                "({ selector, previousEmail }) => { "
                "const input = document.querySelector(selector); "
                "return Boolean("
                "input "
                "&& input.value "
                "&& input.value !== previousEmail"
                "); "
                "}",
                arg={
                    "selector": self._selectors.email_input,
                    "previousEmail": previous_email,
                },
                timeout=self._settings.action_timeout_ms,
            )
        except PlaywrightTimeoutError as exc:
            raise PageLoadTimeoutError("Temporary email was not refreshed in time") from exc

        current_email = await self.read_current_email(page)

        if current_email == previous_email:
            raise ScrapingError("Tempail returned the same email after refresh")

        logger.info(
            "Temporary email refreshed, old=%s new=%s",
            self._mask_email(previous_email),
            self._mask_email(current_email),
        )

        return previous_email, current_email

    async def _wait_for_inbox_state(self, page: Page) -> None:
        try:
            await page.wait_for_function(
                "({ rowsSelector, emptySelector }) => { "
                "const rows = document.querySelectorAll(rowsSelector); "
                "const emptyState = document.querySelector(emptySelector); "
                "return rows.length > 0 || emptyState !== null; "
                "}",
                arg={
                    "rowsSelector": self._selectors.inbox_rows,
                    "emptySelector": self._selectors.empty_inbox,
                },
                timeout=self._settings.action_timeout_ms,
            )
        except PlaywrightTimeoutError as exc:
            raise ElementNotFoundError("Inbox rows and empty state were not found") from exc

    async def _parse_inbox_row(
        self,
        row: Locator,
        index: int,
    ) -> MessageReference:
        raw_id = await row.get_attribute("id")

        if not raw_id:
            raise ScrapingError(f"Inbox row {index} has no id attribute")

        message_id = self._normalize_message_id(raw_id)

        link = row.locator(self._selectors.row_link).first

        if await link.count() == 0:
            raise ScrapingError(f"Email '{message_id}' has no link")

        href = await link.get_attribute("href")

        if not href:
            raise ScrapingError(f"Email '{message_id}' has an empty href")

        sender = await self._read_required_text(
            row.locator(self._selectors.row_sender),
            "email sender",
        )
        received_at = await self._read_required_text(
            row.locator(self._selectors.row_timestamp),
            "email timestamp",
        )

        return MessageReference(
            id=message_id,
            href=href.strip(),
            sender=sender,
            received_at=received_at,
        )

    async def _open_message(self, page: Page, reference: MessageReference) -> None:
        try:
            await page.goto(
                reference.href,
                wait_until="domcontentloaded",
                timeout=self._settings.navigation_timeout_ms,
            )
            await page.locator(self._selectors.message_container).wait_for(
                state="visible",
                timeout=self._settings.action_timeout_ms,
            )
            await page.locator(self._selectors.message_iframe).wait_for(
                state="attached",
                timeout=self._settings.action_timeout_ms,
            )
        except PlaywrightTimeoutError as exc:
            raise PageLoadTimeoutError(f"Email '{reference.id}' loading timed out") from exc

        await self._raise_if_anti_bot(page)

    async def _read_opened_message(
        self,
        page: Page,
        reference: MessageReference,
    ) -> EmailMessage:
        sender = await self._read_message_sender(page=page, fallback=reference.sender)

        received_at = await self._read_optional_text(
            page.locator(self._selectors.message_timestamp)
        )
        if not received_at:
            received_at = reference.received_at

        body = await self._read_message_body(page)

        return EmailMessage(
            id=reference.id,
            sender=sender,
            received_at=received_at,
            body=body,
        )

    async def _read_message_sender(self, page: Page, fallback: str) -> str:
        container = page.locator(self._selectors.message_sender_container)

        await self._wait_visible(container, "message sender container")

        raw_text = (await container.first.inner_text()).strip()

        angle_brackets_match = re.search(r"<\s*([^<>@\s]+@[^<>@\s]+)\s*>", raw_text)
        if angle_brackets_match is not None:
            return angle_brackets_match.group(1).strip()

        email_match = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", raw_text)
        if email_match is not None:
            return email_match.group(0)

        if fallback:
            return fallback

        raise ScrapingError("Could not extract email sender")

    async def _read_message_body(self, page: Page) -> str:
        frame = page.frame_locator(self._selectors.message_iframe)
        body = frame.locator("body > div[dir='ltr']")

        try:
            await body.wait_for(
                state="attached",
                timeout=self._settings.action_timeout_ms,
            )
        except PlaywrightTimeoutError as exc:
            raise ElementNotFoundError("Email iframe body was not found") from exc

        return (await body.inner_text()).strip()

    async def _is_inbox_empty(self, page: Page) -> bool:
        rows = page.locator(self._selectors.inbox_rows)

        if await rows.count() > 0:
            return False

        empty_state = page.locator(self._selectors.empty_inbox)

        if await empty_state.count() == 0:
            return True

        return await empty_state.first.is_visible()

    async def _accept_cookies(self, page: Page) -> None:
        button = page.locator(self._selectors.cookie_accept_button)

        if await button.count() == 0:
            return

        if not await button.first.is_visible():
            return

        try:
            await button.first.click(timeout=2_000)
        except PlaywrightTimeoutError:
            logger.debug("Cookie banner could not be closed")

    async def _wait_visible(self, locator: Locator, element_name: str) -> None:
        try:
            await locator.first.wait_for(
                state="visible",
                timeout=self._settings.action_timeout_ms,
            )
        except PlaywrightTimeoutError as exc:
            raise ElementNotFoundError(f"Could not find visible {element_name}") from exc

    async def _read_required_text(self, locator: Locator, element_name: str) -> str:
        await self._wait_visible(locator, element_name)
        value = (await locator.first.inner_text()).strip()

        if not value:
            raise ScrapingError(f"{element_name} contains an empty value")

        return value

    @staticmethod
    async def _read_optional_text(locator: Locator) -> str:
        if await locator.count() == 0:
            return ""

        return (await locator.first.inner_text()).strip()

    async def _raise_if_anti_bot(self, page: Page) -> None:
        try:
            body_text = (await page.locator("body").inner_text(timeout=2_000)).lower()
        except PlaywrightTimeoutError:
            return

        markers = (
            "verify that you are not a robot",
            "verify you are human",
            "captcha",
            "перевірте, що ви не робот",
            "підтвердьте, що ви не робот",
        )

        if any(marker in body_text for marker in markers):
            raise AntiBotChallengeError("Tempail requested human verification")

    @staticmethod
    def _normalize_message_id(raw_id: str) -> str:
        message_id = raw_id.strip()

        if message_id.startswith("mail_"):
            message_id = message_id.removeprefix("mail_")

        if not message_id:
            raise ScrapingError("Email has an empty id")

        return message_id

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        return re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) is not None

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
