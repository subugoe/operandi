from os import environ
from os.path import join

try:
    from importlib.metadata import distribution as get_distribution
except ImportError:
    from importlib_metadata import distribution as get_distribution

__all__ = [
    "OPERANDI_VERSION"
]

OPERANDI_VERSION = get_distribution('operandi_utils').version
OPERANDI_LOCAL_DIR = environ.get("OCRD_WEBAPI_BASE_DIR", "/tmp/operandi_data")
OPERANDI_LOCAL_DIR_WORKFLOW_JOBS = join(OPERANDI_LOCAL_DIR, "workflow_jobs")
OPERANDI_LOCAL_DIR_WORKFLOWS = join(OPERANDI_LOCAL_DIR, "workflows")
OPERANDI_LOCAL_DIR_WORKSPACES = join(OPERANDI_LOCAL_DIR, "workspaces")
