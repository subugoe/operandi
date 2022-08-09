from pathlib import Path

__all__ = [
    "HPC_HOST",
    "HPC_USERNAME",
    "HPC_KEY_PATH",
    "HPC_HOME_PATH",
    "SCP",
    "SCP_PRESERVE_TIMES",
    "MODE",
    "OPERANDI_DATA_PATH"
]

# HPC related constants
# Must be either gwdu101 or gwdu102 (have /scratch1 access)
# gwdu103 has no access to /scratch1 (have /scratch2 access)
HPC_HOST: str = "gwdu101.gwdg.de"
HPC_USERNAME: str = "mmustaf"
# This is the default key file path
HPC_KEY_PATH: str = f"{Path.home()}/.ssh/gwdg-cluster.pub"
# Home directory inside the HPC environment
HPC_HOME_PATH: str = f"/home/users/{HPC_USERNAME}"

# Secure copy protocol related constants
SCP: str = "ON"
# TODO: Test this inside the HPC environment
SCP_PRESERVE_TIMES: str = "True"
MODE: str = "0755"

# OPERANDI related data is stored inside
OPERANDI_DATA_PATH: str = f"{Path.home()}/operandi-data"
