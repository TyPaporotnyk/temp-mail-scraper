from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class InboxMessage:
    id: str
    sender: str
    subject: str
    received_at: str


@dataclass(slots=True, frozen=True)
class EmailMessage:
    id: str
    sender: str
    subject: str
    received_at: str
    body: str
