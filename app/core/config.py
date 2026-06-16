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
