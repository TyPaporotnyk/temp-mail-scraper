from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class BrowserManagerSettings:
    browser_headless: bool
    browser_storage_state_path: Path
    action_timeout_ms: int
    navigation_timeout_ms: int
    browser_config: dict[str, str]
