from dotenv import load_dotenv
from os import getenv

__all__ = [
    'BASE_DIR',
    'JOBS_ROUTER',
    'WORKFLOWS_ROUTER',
    'WORKSPACES_ROUTER',
]

load_dotenv()

BASE_DIR: str = getenv("OCRD_WEBAPI_BASE_DIR", "/tmp/ocrd-webapi-data")
JOBS_ROUTER: str = getenv("OCRD_WEBAPI_JOBS_ROUTER", "workflow_jobs")
WORKFLOWS_ROUTER: str = getenv("OCRD_WEBAPI_WORKFLOWS_ROUTER", "workflows")
WORKSPACES_ROUTER: str = getenv("OCRD_WEBAPI_WORKSPACES_ROUTER", "workspaces")
