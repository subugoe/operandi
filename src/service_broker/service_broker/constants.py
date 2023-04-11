from dotenv import load_dotenv
from os import environ
from pathlib import Path

__all__ = [
    "DEFAULT_QUEUE_FOR_HARVESTER",
    "DEFAULT_QUEUE_FOR_USERS",
    "HPC_HOME_PATH",
    "HPC_HOST",
    "HPC_KEY_PATH",
    "HPC_USERNAME",
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

# HPC related constants
# Must be either gwdu101 or gwdu102 (have /scratch1 access)
# gwdu103 has no access to /scratch1 (have /scratch2 access)
HPC_HOST: str = environ.get("OPERANDI_HPC_HOST", "gwdu101.gwdg.de")
HPC_USERNAME: str = environ.get("OPERANDI_HPC_USERNAME", "mmustaf")
HPC_KEY_PATH: str = environ.get("OPERANDI_HPC_SSH_KEYPATH", f"{Path.home()}/.ssh/gwdg-cluster.pub")
HPC_HOME_PATH: str = environ.get("OPERANDI_HPC_HOME_PATH", f"/home/users/{HPC_USERNAME}")

# TODO: Use this as a root data directory
OPERANDI_ROOT_DATA_PATH: str = environ.get("OPERANDI_ROOT_DATA_PATH", "/tmp/operandi-data")
