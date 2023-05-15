from datetime import datetime
from dotenv import load_dotenv
from os import getenv
from operandi_utils import OPERANDI_LOGS_DIR

__all__ = [
    'DB_NAME',
    'DB_URL',
    'SERVER_URL',
    'BASE_DIR',
    'JOBS_ROUTER',
    "LOG_FILE_PATH",
    "LOG_LEVEL",
    'WORKFLOWS_ROUTER',
    'WORKSPACES_ROUTER',
]

# variables for local testing are read from .env in base-dir with `load_dotenv()`
load_dotenv()

current_time = datetime.now().strftime("%Y-%m-%d_%H-%M")
LOG_FILE_PATH: str = f"{OPERANDI_LOGS_DIR}/server_{current_time}.log"
LOG_LEVEL: str = "INFO"

# TODO: This constant value takes a lot of different values based on the environment
#  that it is almost impossible to know it's value. Figured out after spending hours on the code.
#  This must be configurable in a better way...
#  consider: https://fastapi.tiangolo.com/advanced/settings/
DB_URL: str = getenv("OCRD_WEBAPI_DB_URL", "mongodb://localhost:27018")
DB_NAME: str = getenv("OCRD_WEBAPI_DB_NAME", "ocrd-webapi-db")

# The SERVER_URL, BASE_DIR and *_ROUTERS are used by the ResourceManagers
SERVER_URL: str = getenv("OCRD_WEBAPI_SERVER_PATH", "http://localhost:8000")
BASE_DIR: str = getenv("OCRD_WEBAPI_BASE_DIR", "/tmp/ocrd-webapi-data")

# Routers are basically the folder names placed under the BASE_DIR
# TODO: Use `JOBS_ROUTER`. Jobs must not be related to a specific workflow folder (for better consistency)
JOBS_ROUTER: str = getenv("OCRD_WEBAPI_JOBS_ROUTER", "jobs")
WORKFLOWS_ROUTER: str = getenv("OCRD_WEBAPI_WORKFLOWS_ROUTER", "workflows")
WORKSPACES_ROUTER: str = getenv("OCRD_WEBAPI_WORKSPACES_ROUTER", "workspaces")
# Warning: Don't change the router defaults till everything is configured properly
