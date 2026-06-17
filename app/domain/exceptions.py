class TempMailError(Exception):
    code = "temp_mail_error"
    default_message = "Temp mail operation failed"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class BrowserUnavailableError(TempMailError):
    code = "browser_unavailable"
    default_message = "Browser is unavailable"


class BrowserSessionError(TempMailError):
    code = "browser_session_error"
    default_message = "Browser session is unavailable"


class PageLoadTimeoutError(TempMailError):
    code = "page_load_timeout"
    default_message = "Page loading timed out"


class ElementNotFoundError(TempMailError):
    code = "element_not_found"
    default_message = "Expected page element was not found"


class EmailNotFoundError(TempMailError):
    code = "email_not_found"
    default_message = "Email was not found"


class ScrapingError(TempMailError):
    code = "scraping_error"
    default_message = "Could not extract data from Tempail"


class AntiBotChallengeError(TempMailError):
    code = "anti_bot_challenge"
    default_message = "Tempail requested human verification"


class InvalidEmailAddressError(TempMailError):
    code = "invalid_email_address"
    default_message = "Temporary email address is invalid"


class InboxUnavailableError(TempMailError):
    code = "inbox_unavailable"
    default_message = "Temp mail inbox is unavailable"
