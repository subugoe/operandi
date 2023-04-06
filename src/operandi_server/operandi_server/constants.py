import datetime
from os import environ
from pathlib import Path

__all__ = [
    "DEFAULT_QUEUE_FOR_HARVESTER",
    "DEFAULT_QUEUE_FOR_USERS",
    "LOG_FOLDER_PATH",
    "LOG_FILE_PATH",
    "LOG_LEVEL",
    "OPERANDI_ROOT_DATA_PATH",
    "SERVER_HOST",
    "SERVER_PORT",
    "LIVE_SERVER_URL"
]

DEFAULT_QUEUE_FOR_HARVESTER: str = "operandi-for-harvester"
DEFAULT_QUEUE_FOR_USERS: str = "operandi-for-users"

LOG_FOLDER_PATH: str = environ.get("OPERANDI_LOGS_DIR", f"{Path.home()}/operandi-logs")
Path(LOG_FOLDER_PATH).mkdir(parents=True, exist_ok=True)

current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
LOG_FILE_PATH: str = f"{LOG_FOLDER_PATH}/server_{current_time}.log"
LOG_LEVEL: str = "INFO"

# TODO: Use this as a root data directory
OPERANDI_ROOT_DATA_PATH: str = "/tmp/operandi-data"

SERVER_HOST: str = "localhost"
SERVER_PORT: int = 8000
LIVE_SERVER_URL: str = environ.get("OPERANDI_LIVE_SERVER_URL", f"http://{SERVER_HOST}:{SERVER_PORT}")
