from pkg_resources import resource_filename
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
import os
import logging
from pathlib import Path

__all__ = [
    "HPC_HOST",
    "HPC_USERNAME",
    "HPC_KEY_PATH",
    "HPC_HOME_PATH",
    "SCP",
    "SCP_PRESERVE_TIMES",
    "MODE",
    "DB_URL",
    "OPERANDI_DATA_PATH",
    "JOBS_DIR",
    "WORKFLOWS_DIR",
    "WORKSPACES_DIR",
    "LOG_LEVEL",
    "LOG_FORMAT"
]

TOML_FILENAME: str = resource_filename(__name__, 'config.toml')
TOML_FD = open(TOML_FILENAME, mode='rb')
TOML_CONFIG = tomllib.load(TOML_FD)
TOML_FD.close()

# HPC related constants
# Must be either gwdu101 or gwdu102 (have /scratch1 access)
# gwdu103 has no access to /scratch1 (have /scratch2 access)
HPC_HOST: str = TOML_CONFIG["hpc_host"]
HPC_USERNAME: str = TOML_CONFIG["hpc_username"]
# This is the default key file path
HPC_KEY_PATH: str = f"{Path.home()}/.ssh/gwdg-cluster.pub"
# Home directory inside the HPC environment
HPC_HOME_PATH: str = f"/home/users/{HPC_USERNAME}"

# Secure copy protocol related constants
SCP: str = TOML_CONFIG["scp"]
# TODO: Test this inside the HPC environment
SCP_PRESERVE_TIMES: str = eval(TOML_CONFIG["scp_preserve_times"])
MODE: str = TOML_CONFIG["mode"]

# OPERANDI related data is stored inside
OPERANDI_DATA_PATH: str = TOML_CONFIG["server_data_path"]
JOBS_DIR: str = os.path.join(OPERANDI_DATA_PATH, "jobs")
WORKFLOWS_DIR: str = os.path.join(OPERANDI_DATA_PATH, "workflows")
WORKSPACES_DIR: str = os.path.join(OPERANDI_DATA_PATH, "workspaces")
DB_URL: str = TOML_CONFIG["mongodb_url"]

LOG_FORMAT: str = '%(levelname) -10s %(asctime)s %(name) -30s %(funcName) -35s %(lineno) -5d: %(message)s'
LOG_LEVEL: int = logging.INFO
