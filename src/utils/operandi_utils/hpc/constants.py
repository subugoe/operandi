from dotenv import load_dotenv
from os import environ
from os.path import join

__all__ = [
    "OPERANDI_HPC_DIR_BATCH_SCRIPTS",
    "OPERANDI_HPC_DIR_HOME_USER",
    "OPERANDI_HPC_DIR_HOME_SCRATCH",
    "OPERANDI_HPC_DIR_PROJECT",
    "OPERANDI_HPC_DIR_SLURM_WORKSPACES",
    "OPERANDI_HPC_HOST",
    "OPERANDI_HPC_HOST_PROXY",
    "OPERANDI_HPC_HOST_TRANSFER",
    "OPERANDI_HPC_SSH_KEYPATH",
    "OPERANDI_HPC_USERNAME"
]

load_dotenv()

# HPC related constants
OPERANDI_HPC_HOST: str = environ.get("OPERANDI_HPC_HOST", "login-mdc.hpc.gwdg.de")
OPERANDI_HPC_HOST_PROXY: str = environ.get("OPERANDI_HPC_HOST_PROXY", "login.gwdg.de")
OPERANDI_HPC_HOST_TRANSFER: str = environ.get("OPERANDI_HPC_HOST_TRANSFER", "transfer.gwdg.de")
OPERANDI_HPC_SSH_KEYPATH: str = environ.get("OPERANDI_HPC_SSH_KEYPATH")

OPERANDI_HPC_USERNAME: str = environ.get("OPERANDI_HPC_USERNAME", "mmustaf")
OPERANDI_HPC_DIR_HOME_USER: str = environ.get(
    "OPERANDI_HPC_DIR_HOME_USER",
    f"/home/users/{OPERANDI_HPC_USERNAME}"
)
OPERANDI_HPC_DIR_HOME_SCRATCH: str = environ.get(
    "OPERANDI_HPC_DIR_HOME_SCRATCH",
    f"/scratch1/users/{OPERANDI_HPC_USERNAME}"
)
OPERANDI_HPC_DIR_PROJECT: str = environ.get(
    "OPERANDI_HPC_DIR_PROJECT",
    f"{OPERANDI_HPC_DIR_HOME_USER}/operandi"
)

OPERANDI_HPC_DIR_BATCH_SCRIPTS = join(OPERANDI_HPC_DIR_PROJECT, "batch_scripts")
OPERANDI_HPC_DIR_SLURM_WORKSPACES = join(OPERANDI_HPC_DIR_PROJECT, "slurm_workspaces")
