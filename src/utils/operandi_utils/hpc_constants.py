from dotenv import load_dotenv
from os import environ
from pathlib import Path

__all__ = [
    "OPERANDI_HPC_HOME_PATH",
    "OPERANDI_HPC_HOME_PATH_SCRATCH",
    "OPERANDI_HPC_HOST",
    "OPERANDI_HPC_HOST_PROXY",
    "OPERANDI_HPC_HOST_TRANSFER",
    "OPERANDI_HPC_SSH_KEYPATH",
    "OPERANDI_HPC_USERNAME"
]

load_dotenv()

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
