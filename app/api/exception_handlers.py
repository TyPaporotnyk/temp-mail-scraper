import logging
from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import (
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_CONTENT,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_502_BAD_GATEWAY,
    HTTP_503_SERVICE_UNAVAILABLE,
    HTTP_504_GATEWAY_TIMEOUT,
)

from app.domain.exceptions import (
    AntiBotChallengeError,
    BrowserSessionError,
    BrowserUnavailableError,
    ElementNotFoundError,
    EmailNotFoundError,
    InboxUnavailableError,
    InvalidEmailAddressError,
    PageLoadTimeoutError,
    ScrapingError,
    TempMailError,
)

logger = logging.getLogger(__name__)


def get_temp_mail_error_status_code(
    exception: TempMailError,
) -> int:
    match exception:
        case EmailNotFoundError():
            return HTTP_404_NOT_FOUND

        case (
            BrowserUnavailableError()
            | BrowserSessionError()
            | AntiBotChallengeError()
            | InboxUnavailableError()
        ):
            return HTTP_503_SERVICE_UNAVAILABLE

        case PageLoadTimeoutError():
            return HTTP_504_GATEWAY_TIMEOUT

        case ElementNotFoundError() | InvalidEmailAddressError() | ScrapingError():
            return HTTP_502_BAD_GATEWAY

        case _:
            return HTTP_500_INTERNAL_SERVER_ERROR


def build_error_response(
    *,
    code: str,
    message: str,
) -> dict[str, Any]:
    error: dict[str, Any] = {
        "code": code,
        "message": message,
    }

    return {"error": error}


async def temp_mail_exception_handler(
    request: Request,
    exception: TempMailError,
) -> JSONResponse:
    status_code = get_temp_mail_error_status_code(exception)

    log_method = logger.error if status_code >= HTTP_500_INTERNAL_SERVER_ERROR else logger.warning

    log_method(
        "TempMail request failed: method=%s path=%s status=%s code=%s message=%s",
        request.method,
        request.url.path,
        status_code,
        exception.code,
        exception.message,
        exc_info=status_code >= HTTP_500_INTERNAL_SERVER_ERROR,
    )

    return JSONResponse(
        status_code=status_code,
        content=build_error_response(
            code=exception.code,
            message=exception.message,
        ),
    )


async def validation_exception_handler(
    request: Request,
    exception: RequestValidationError,
) -> JSONResponse:
    logger.warning(
        "Request validation failed: method=%s path=%s",
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_CONTENT,
        content=build_error_response(
            code="validation_error",
            message="Request validation failed",
        ),
    )


async def http_exception_handler(
    request: Request,
    exception: StarletteHTTPException,
) -> JSONResponse:
    logger.warning(
        "HTTP error: method=%s path=%s status=%s",
        request.method,
        request.url.path,
        exception.status_code,
    )

    message = exception.detail if isinstance(exception.detail, str) else "HTTP request failed"

    return JSONResponse(
        status_code=exception.status_code,
        content=build_error_response(
            code="http_error",
            message=message,
        ),
        headers=exception.headers,
    )


async def unexpected_exception_handler(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    logger.exception(
        "Unhandled exception: method=%s path=%s",
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content=build_error_response(
            code="internal_server_error",
            message="Internal server error",
        ),
    )


def register_exception_handlers(
    app: FastAPI,
) -> None:
    app.add_exception_handler(
        TempMailError,
        cast(Any, temp_mail_exception_handler),
    )
    app.add_exception_handler(
        RequestValidationError,
        cast(Any, validation_exception_handler),
    )
    app.add_exception_handler(
        StarletteHTTPException,
        cast(Any, http_exception_handler),
    )
    app.add_exception_handler(
        Exception,
        unexpected_exception_handler,
    )
