from dotenv import load_dotenv
from os import environ
from os.path import join
from pathlib import Path

__all__ = [
    "OCRD_WEBAPI_DB_NAME",
    "OCRD_WEBAPI_DB_URL",
    "OCRD_WEBAPI_PASSWORD",
    "OCRD_WEBAPI_USERNAME",

    "OPERANDI_HPC_HOME_PATH",
    "OPERANDI_HPC_HOST",
    "OPERANDI_HPC_HOST_PROXY",
    "OPERANDI_HPC_HOST_TRANSFER",
    "OPERANDI_HPC_SSH_KEYPATH",
    "OPERANDI_HPC_USERNAME",

    "OPERANDI_LOCAL_SERVER_ADDR",
    "OPERANDI_LIVE_SERVER_ADDR",

    "OPERANDI_TESTS_LOCAL_DIR",
    "OPERANDI_TESTS_LOCAL_DIR_WORKFLOW_JOBS",
    "OPERANDI_TESTS_LOCAL_DIR_WORKFLOWS",
    "OPERANDI_TESTS_LOCAL_DIR_WORKSPACES",

    "OPERANDI_TESTS_HPC_DIR",
    "OPERANDI_TESTS_HPC_DIR_BATCH_SCRIPTS",
    "OPERANDI_TESTS_HPC_DIR_WORKFLOW_JOBS",
    "OPERANDI_TESTS_HPC_DIR_WORKFLOWS",
    "OPERANDI_TESTS_HPC_DIR_WORKSPACES"
]

load_dotenv()

OCRD_WEBAPI_DB_NAME = environ.get("OCRD_WEBAPI_DB_NAME", "test_operandi_db")
OCRD_WEBAPI_DB_URL = environ.get("OCRD_WEBAPI_DB_URL", "mongodb://localhost:27018")
OCRD_WEBAPI_USERNAME = environ.get("OCRD_WEBAPI_USERNAME", "test")
OCRD_WEBAPI_PASSWORD = environ.get("OCRD_WEBAPI_PASSWORD", "test")

# HPC related constants
# The host must be either `gwdu101.gwdg.de` or `gwdu102.gwdg.de` (to have /scratch1 access)
# `gwdu103.gwdg.de` has no access to /scratch1 (but have /scratch2 access)
# login-mdc.hpc.gwdg.de (gwdu101 and gwdu102)
OPERANDI_HPC_HOST: str = environ.get("OPERANDI_HPC_HOST", "login-mdc.hpc.gwdg.de")
OPERANDI_HPC_HOST_PROXY: str = environ.get("OPERANDI_HPC_HOST_PROXY", "login.gwdg.de")
OPERANDI_HPC_HOST_TRANSFER: str = environ.get("OPERANDI_HPC_HOST_TRANSFER", "transfer.gwdg.de")
OPERANDI_HPC_USERNAME: str = environ.get("OPERANDI_HPC_USERNAME", "mmustaf")
OPERANDI_HPC_SSH_KEYPATH: str = environ.get(
    "OPERANDI_HPC_SSH_KEYPATH",
    f"{Path.home()}/.ssh/gwdg-cluster.pub"
)
OPERANDI_HPC_HOME_PATH: str = environ.get(
    "OPERANDI_HPC_HOME_PATH",
    f"/home/users/{OPERANDI_HPC_USERNAME}"
)
OPERANDI_HPC_HOME_PATH_SCRATCH: str = environ.get(
    "OPERANDI_HPC_HOME_PATH_SCRATCH",
    f"/scratch1/users/{OPERANDI_HPC_USERNAME}"
)

OPERANDI_LOCAL_SERVER_ADDR = environ.get("OPERANDI_LOCAL_SERVER_URL", f"http://localhost:48000")
OPERANDI_LIVE_SERVER_ADDR = environ.get("OPERANDI_LIVE_SERVER_URL", OPERANDI_LOCAL_SERVER_ADDR)

OPERANDI_TESTS_LOCAL_DIR = environ.get("OPERANDI_TESTS_DIR", "/tmp/operandi_tests")
OPERANDI_TESTS_LOCAL_DIR_WORKFLOW_JOBS = join(OPERANDI_TESTS_LOCAL_DIR, "workflow_jobs")
OPERANDI_TESTS_LOCAL_DIR_WORKFLOWS = join(OPERANDI_TESTS_LOCAL_DIR, "workflows")
OPERANDI_TESTS_LOCAL_DIR_WORKSPACES = join(OPERANDI_TESTS_LOCAL_DIR, "workspaces")

OPERANDI_TESTS_HPC_DIR = join(OPERANDI_HPC_HOME_PATH, "tests")
OPERANDI_TESTS_HPC_DIR_BATCH_SCRIPTS = join(OPERANDI_TESTS_HPC_DIR, "batch_scripts")
OPERANDI_TESTS_HPC_DIR_WORKFLOW_JOBS = join(OPERANDI_TESTS_HPC_DIR, "workflow_jobs")
OPERANDI_TESTS_HPC_DIR_WORKFLOWS = join(OPERANDI_TESTS_HPC_DIR, "workflows")
OPERANDI_TESTS_HPC_DIR_WORKSPACES = join(OPERANDI_TESTS_HPC_DIR, "workspaces")
