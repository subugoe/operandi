from datetime import datetime
from dotenv import load_dotenv
from os import getenv
from operandi_utils import OPERANDI_LOGS_DIR

__all__ = [
    'SERVER_URL',
    "LOG_FILE_PATH",
    "LOG_LEVEL"
]

# variables for local testing are read from .env in base-dir with `load_dotenv()`
load_dotenv()

current_time = datetime.now().strftime("%Y-%m-%d_%H-%M")
LOG_FILE_PATH: str = f"{OPERANDI_LOGS_DIR}/server_{current_time}.log"
LOG_LEVEL: str = "INFO"

# The SERVER_URL, BASE_DIR and *_ROUTERS are used by the ResourceManagers
SERVER_URL: str = getenv("OPERANDI_SERVER_URL_LIVE")
