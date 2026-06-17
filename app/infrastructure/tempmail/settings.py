from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class TempMailClientSettings:
    tempail_url: str
    action_timeout_ms: int
    navigation_timeout_ms: int
