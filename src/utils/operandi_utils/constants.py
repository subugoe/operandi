from datetime import datetime
from dotenv import load_dotenv
from os import environ
from pathlib import Path

try:
    from importlib.metadata import distribution as get_distribution
except ImportError:
    from importlib_metadata import distribution as get_distribution

__all__ = [
    "LOG_FILE_PATH_BROKER",
    "LOG_FILE_PATH_HARVESTER",
    "LOG_FILE_PATH_SERVER",
    "LOG_FILE_PATH_WORKER_PREFIX",
    "LOG_FORMAT",
    "LOG_LEVEL_BROKER",
    "LOG_LEVEL_HARVESTER",
    "LOG_LEVEL_RMQ_CONSUMER",
    "LOG_LEVEL_RMQ_PUBLISHER",
    "LOG_LEVEL_SERVER",
    "LOG_LEVEL_WORKER",
    "OPERANDI_LOGS_DIR",
    "OPERANDI_VERSION",
    "SERVER_BASE_DIR",
    "SERVER_WORKFLOW_JOBS_ROUTER",
    "SERVER_WORKFLOWS_ROUTER",
    "SERVER_WORKSPACES_ROUTER"
]

load_dotenv()

OPERANDI_VERSION = get_distribution('operandi_utils').version

# Server file handling constants
SERVER_BASE_DIR: str = environ.get("OPERANDI_SERVER_BASE_DIR", None)
if not SERVER_BASE_DIR:
    raise ValueError("Environment variable not set: OPERANDI_SERVER_BASE_DIR")
SERVER_WORKFLOW_JOBS_ROUTER: str = "workflow_jobs"
SERVER_WORKFLOWS_ROUTER: str = "workflows"
SERVER_WORKSPACES_ROUTER: str = "workspaces"

# Modules logging constants
OPERANDI_LOGS_DIR: str = environ.get("OPERANDI_LOGS_DIR", None)
if not OPERANDI_LOGS_DIR:
    raise ValueError("Environment variable not set: OPERANDI_LOGS_DIR")
Path(OPERANDI_LOGS_DIR).mkdir(mode=0o777, parents=True, exist_ok=True)
Path(OPERANDI_LOGS_DIR).chmod(mode=0o777)

current_time = datetime.now().strftime("%Y-%m-%d_%H-%M")
LOG_FILE_PATH_SERVER: str = f"{OPERANDI_LOGS_DIR}/server_{current_time}.log"
LOG_FILE_PATH_HARVESTER: str = f"{OPERANDI_LOGS_DIR}/harvester_{current_time}.log"
LOG_FILE_PATH_BROKER: str = f"{OPERANDI_LOGS_DIR}/broker_{current_time}.log"
LOG_FILE_PATH_WORKER_PREFIX: str = f"{OPERANDI_LOGS_DIR}/worker_{current_time}"

LOG_FORMAT: str = "%(levelname) -7s %(asctime)s %(name) -30s %(funcName) -35s %(lineno) -5d: %(message)s"
LOG_LEVEL_SERVER: str = "INFO"
LOG_LEVEL_HARVESTER: str = "INFO"
LOG_LEVEL_BROKER: str = "INFO"
LOG_LEVEL_WORKER: str = "INFO"
LOG_LEVEL_RMQ_CONSUMER: str = "INFO"
LOG_LEVEL_RMQ_PUBLISHER: str = "INFO"
