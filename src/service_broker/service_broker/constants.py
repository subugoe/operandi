from pkg_resources import resource_filename
import tomli
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

TOML_FILENAME: str = resource_filename(__name__, 'config.toml')
TOML_FD = open(TOML_FILENAME, mode='rb')
TOML_CONFIG = tomli.load(TOML_FD)
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
OPERANDI_DATA_PATH: str = f"{Path.home()}/operandi-data"
