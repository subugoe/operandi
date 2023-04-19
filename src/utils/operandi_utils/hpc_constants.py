from dotenv import load_dotenv
from os import environ
from pathlib import Path

__all__ = [
    "OPERANDI_HPC_HOME_PATH",
    "OPERANDI_HPC_HOST",
    "OPERANDI_HPC_SSH_KEYPATH",
    "OPERANDI_HPC_USERNAME"
]

load_dotenv()

# HPC related constants
# Must be either gwdu101 or gwdu102 (have /scratch1 access)
# gwdu103 has no access to /scratch1 (have /scratch2 access)
OPERANDI_HPC_HOST: str = environ.get("OPERANDI_HPC_HOST", "gwdu101.gwdg.de")
OPERANDI_HPC_USERNAME: str = environ.get("OPERANDI_HPC_USERNAME", "mmustaf")
OPERANDI_HPC_SSH_KEYPATH: str = environ.get("OPERANDI_HPC_SSH_KEYPATH", f"{Path.home()}/.ssh/gwdg-cluster.pub")
OPERANDI_HPC_HOME_PATH: str = environ.get("OPERANDI_HPC_HOME_PATH", f"/home/users/{OPERANDI_HPC_USERNAME}")
