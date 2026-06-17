import logging
from pathlib import Path

from starlette.config import Config

logger = logging.getLogger(__name__)
config = Config(".env")

BASE_DIR = Path(__file__).resolve().parent.parent.parent

APP_NAME = config("APP_NAME")
APP_VERSION = config("APP_VERSION")
APP_DOCS_URL = config("APP_DOCS_URL")

LOG_LEVEL = config("LOG_LEVEL")

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

BROWSER_HEADLESS = "virtual"
BROWSER_HUMANIZE = True
BROWSER_STORAGE_STATE_PATH = DATA_DIR / "state.json"
ACTION_TIMEOUT_MS = 30_000
NAVIGATION_TIMEOUT_MS = 30_000
BROWSER_CONFIG = {
    "window.outerHeight": 1056,
    "window.outerWidth": 1920,
    "window.innerHeight": 1008,
    "window.innerWidth": 1920,
    "window.history.length": 4,
    "navigator.userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "navigator.appCodeName": "Mozilla",
    "navigator.appName": "Netscape",
    "navigator.appVersion": "5.0 (Windows)",
    "navigator.oscpu": "Windows NT 10.0; Win64; x64",
    "navigator.language": "en-US",
    "navigator.languages": ["en-US"],
    "navigator.platform": "Win32",
    "navigator.hardwareConcurrency": 12,
    "navigator.product": "Gecko",
    "navigator.productSub": "20030107",
    "navigator.maxTouchPoints": 10,
}
