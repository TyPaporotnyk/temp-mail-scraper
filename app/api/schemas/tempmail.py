from pydantic import BaseModel, ConfigDict


class EmailAddressResponse(BaseModel):
    email: str


class InboxItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    sender: str
    received_at: str


class InboxResponse(BaseModel):
    items: list[InboxItemResponse]


class EmailDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    sender: str
    received_at: str
    body: str
