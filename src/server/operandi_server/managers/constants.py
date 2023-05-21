from dotenv import load_dotenv
from os import environ
from os.path import join

__all__ = [
    'BASE_DIR',
    'JOBS_ROUTER',
    'WORKFLOWS_ROUTER',
    'WORKSPACES_ROUTER',
]

load_dotenv()

BASE_DIR = environ.get("OPERANDI_SERVER_BASE_DIR")
JOBS_ROUTER = join(BASE_DIR, "workflow_jobs")
WORKFLOWS_ROUTER = join(BASE_DIR, "workflows")
WORKSPACES_ROUTER = join(BASE_DIR, "workspaces")
