import datetime
from os import mkdir
from os.path import exists

__all__ = [
    "DB_URL",
    "DEFAULT_QUEUE_FOR_HARVESTER",
    "DEFAULT_QUEUE_FOR_USERS",
    "LOG_FILE_PATH",
    "LOG_LEVEL",
    "OPERANDI_ROOT_DATA_PATH",
    "SERVER_HOST",
    "SERVER_PORT"
]

DB_URL: str = "mongodb://localhost:27018"
DEFAULT_QUEUE_FOR_HARVESTER: str = "operandi-for-harvester"
DEFAULT_QUEUE_FOR_USERS: str = "operandi-for-users"

LOG_FOLDER_PATH: str = "/tmp/operandi-logs"
if not exists(LOG_FOLDER_PATH):
    mkdir(LOG_FOLDER_PATH)

current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M")
LOG_FILE_PATH: str = f"{LOG_FOLDER_PATH}/operandi-server_{current_time}.log"
LOG_LEVEL: str = "INFO"


# TODO: Use this as a root data directory
OPERANDI_ROOT_DATA_PATH: str = "/tmp/operandi-data"

SERVER_HOST: str = "localhost"
SERVER_PORT: int = 8000
