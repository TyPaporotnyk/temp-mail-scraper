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
    default_message = "Browser session is invalid"
