from os import environ
from pathlib import Path

__all__ = [
    "OPERANDI_HPC_HOST",
    "OPERANDI_HPC_HOME_PATH",
    "OPERANDI_HPC_SSH_KEYPATH",
    "OPERANDI_HPC_USERNAME"
]

# HPC related configurations
OPERANDI_HPC_HOST = environ.get("OPERANDI_HPC_HOST", "gwdu101.gwdg.de")
OPERANDI_HPC_SSH_KEYPATH = environ.get("OPERANDI_HPC_SSH_KEYPATH", f"{Path.home()}/.ssh/gwdg-cluster.pub")
OPERANDI_HPC_USERNAME = environ.get("OPERANDI_HPC_USERNAME", "mmustaf")
OPERANDI_HPC_HOME_PATH = environ.get("OPERANDI_HPC_HOME_PATH", f"/home/users/{OPERANDI_HPC_USERNAME}")
