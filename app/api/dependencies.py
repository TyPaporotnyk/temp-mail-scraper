from typing import cast

from fastapi import Request

from app.core.container import ApplicationContainer
from app.services.tempmail import TempMailService


def get_container(
    request: Request,
) -> ApplicationContainer:
    return cast(
        ApplicationContainer,
        request.app.state.container,
    )


def get_temp_mail_service(
    request: Request,
) -> TempMailService:
    container = get_container(request)

    return container.temp_mail_service
