import datetime
from os import environ
from pathlib import Path

__all__ = [
    "DB_URL",
    "DEFAULT_QUEUE_FOR_HARVESTER",
    "DEFAULT_QUEUE_FOR_USERS",
    "HPC_HOME_PATH",
    "HPC_HOST",
    "HPC_KEY_PATH",
    "HPC_USERNAME",
    "LOG_FOLDER_PATH",
    "LOG_FILE_PATH",
    "LOG_LEVEL",
    "LOG_LEVEL_WORKER",
    "OPERANDI_ROOT_DATA_PATH"
]

DB_URL: str = "mongodb://localhost:27018"
DEFAULT_QUEUE_FOR_HARVESTER: str = "operandi-for-harvester"
DEFAULT_QUEUE_FOR_USERS: str = "operandi-for-users"

LOG_FOLDER_PATH: str = environ.get("OPERANDI_LOGS_DIR", f"{Path.home()}/operandi-logs")
Path(LOG_FOLDER_PATH).mkdir(parents=True, exist_ok=True)

current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
LOG_FILE_PATH: str = f"{LOG_FOLDER_PATH}/broker_{current_time}.log"
LOG_LEVEL: str = "INFO"
LOG_LEVEL_WORKER: str = "INFO"

# HPC related constants
# Must be either gwdu101 or gwdu102 (have /scratch1 access)
# gwdu103 has no access to /scratch1 (have /scratch2 access)
HPC_HOST: str = "gwdu101.gwdg.de"
HPC_USERNAME: str = "mmustaf"
# This is the default key file path
HPC_KEY_PATH: str = f"{Path.home()}/.ssh/gwdg-cluster.pub"
# Home directory inside the HPC environment
HPC_HOME_PATH: str = f"/home/users/{HPC_USERNAME}"

# TODO: Use this as a root data directory
OPERANDI_ROOT_DATA_PATH: str = "/tmp/operandi-data"
