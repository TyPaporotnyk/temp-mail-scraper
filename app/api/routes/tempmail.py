from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_temp_mail_service
from app.api.schemas.tempmail import (
    EmailAddressResponse,
    EmailDetailResponse,
    InboxItemResponse,
    InboxResponse,
)
from app.services.tempmail import TempMailService

router = APIRouter(
    prefix="/api",
    tags=["Temp mail"],
)

TempMailServiceDependency = Annotated[
    TempMailService,
    Depends(get_temp_mail_service),
]


@router.get(
    "/email",
    response_model=EmailAddressResponse,
)
async def get_current_email(
    service: TempMailServiceDependency,
) -> EmailAddressResponse:
    email = await service.get_current_email()

    return EmailAddressResponse(email=email)


@router.get(
    "/inbox",
    response_model=InboxResponse,
)
async def get_inbox(
    service: TempMailServiceDependency,
) -> InboxResponse:
    messages = await service.get_inbox()

    return InboxResponse(items=[InboxItemResponse.model_validate(message) for message in messages])


@router.get(
    "/email/{message_id}",
    response_model=EmailDetailResponse,
)
async def get_email(
    message_id: str,
    service: TempMailServiceDependency,
) -> EmailDetailResponse:
    message = await service.get_email(message_id)

    return EmailDetailResponse.model_validate(message)


@router.post(
    "/email/refresh",
    response_model=EmailAddressResponse,
)
async def refresh_email(
    service: TempMailServiceDependency,
) -> EmailAddressResponse:
    email = await service.refresh_email()

    return EmailAddressResponse(email=email)
