from dataclasses import dataclass

from app.infrastructure.browser.manager import BrowserManager
from app.infrastructure.tempmail.client import TempMailClient
from app.services.tempmail import TempMailService


@dataclass(slots=True)
class ApplicationContainer:
    browser_manager: BrowserManager
    temp_mail_client: TempMailClient
    temp_mail_service: TempMailService
