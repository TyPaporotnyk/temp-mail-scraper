from dataclasses import dataclass

from app.domain.models import EmailMessage, InboxMessage
from app.infrastructure.tempmail.client import TempMailClient


@dataclass(slots=True)
class TempMailService:
    client: TempMailClient

    async def get_current_email(self) -> str:
        return await self.client.get_current_email()

    async def get_inbox(self) -> list[InboxMessage]:
        return await self.client.list_messages()

    async def get_email(
        self,
        message_id: str,
    ) -> EmailMessage:
        return await self.client.get_message(message_id)

    async def refresh_email(self) -> str:
        return await self.client.refresh_email()
