from datetime import datetime
from dotenv import load_dotenv
from os import getenv, makedirs
from os.path import join
from operandi_utils import OPERANDI_LOGS_DIR
try:
    from tests.constants import OPERANDI_SERVER_URL_LIVE
except Exception as e:
    OPERANDI_SERVER_URL_LIVE = "http://localhost:8000"

__all__ = [
    "BASE_DIR",
    "DEFAULT_FILE_GRP",
    "DEFAULT_METS_BASENAME",
    "LOG_FILE_PATH",
    "LOG_LEVEL",
    "SERVER_URL",
    "WORKFLOW_JOBS_ROUTER",
    "WORKFLOWS_ROUTER",
    "WORKSPACES_ROUTER"
]

# variables for local testing are read from .env in base-dir with `load_dotenv()`
load_dotenv()

current_time = datetime.now().strftime("%Y-%m-%d_%H-%M")
LOG_FILE_PATH: str = f"{OPERANDI_LOGS_DIR}/server_{current_time}.log"
LOG_LEVEL: str = "INFO"

# TODO: Revisit this, temporal fix for the test environment
SERVER_URL: str = getenv("OPERANDI_SERVER_URL_LIVE", OPERANDI_SERVER_URL_LIVE)

BASE_DIR: str = getenv("OPERANDI_SERVER_BASE_DIR", "/tmp/operandi_data")
WORKFLOW_JOBS_ROUTER: str = "workflow_jobs"
WORKFLOWS_ROUTER: str = "workflows"
WORKSPACES_ROUTER: str = "workspaces"

makedirs(name=join(BASE_DIR, WORKFLOW_JOBS_ROUTER), mode=0o777, exist_ok=True)
makedirs(name=join(BASE_DIR, WORKFLOWS_ROUTER), mode=0o777, exist_ok=True)
makedirs(name=join(BASE_DIR, WORKSPACES_ROUTER), mode=0o777, exist_ok=True)

DEFAULT_FILE_GRP: str = "DEFAULT"
DEFAULT_METS_BASENAME: str = "mets.xml"
