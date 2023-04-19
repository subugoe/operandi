from dotenv import load_dotenv
from os import environ
from pathlib import Path

__all__ = [
    "DEFAULT_QUEUE_FOR_HARVESTER",
    "DEFAULT_QUEUE_FOR_USERS",
    "LOG_FOLDER_PATH",
    "LOG_LEVEL",
    "LOG_LEVEL_WORKER",
    "OPERANDI_ROOT_DATA_PATH"
]

load_dotenv()

DEFAULT_QUEUE_FOR_HARVESTER: str = "operandi-for-harvester"
DEFAULT_QUEUE_FOR_USERS: str = "operandi-for-users"

LOG_FOLDER_PATH: str = environ.get("OPERANDI_LOGS_DIR", f"{Path.home()}/operandi-logs")
Path(LOG_FOLDER_PATH).mkdir(parents=True, exist_ok=True)

LOG_LEVEL: str = "INFO"
LOG_LEVEL_WORKER: str = "INFO"

# TODO: Use this as a root data directory
OPERANDI_ROOT_DATA_PATH: str = environ.get("OPERANDI_ROOT_DATA_PATH", "/tmp/operandi-data")
