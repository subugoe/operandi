from dotenv import load_dotenv
from os import environ

__all__ = [
    'BASE_DIR',
    'DEFAULT_FILE_GRP',
    'DEFAULT_METS_BASENAME',
    'LOG_LEVEL',
    'WORKFLOW_JOBS_ROUTER',
    'WORKFLOWS_ROUTER',
    'WORKSPACES_ROUTER',
]

load_dotenv()

DEFAULT_FILE_GRP: str = "DEFAULT"
DEFAULT_METS_BASENAME: str = "mets.xml"
LOG_LEVEL: str = "INFO"

BASE_DIR = environ.get("OPERANDI_SERVER_BASE_DIR", "/tmp/operandi_data")
WORKFLOW_JOBS_ROUTER: str = "workflow_jobs"
WORKFLOWS_ROUTER: str = "workflows"
WORKSPACES_ROUTER: str = "workspaces"
