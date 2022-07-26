__all__ = [
    "HPC_HOST",
    "HPC_USERNAME",
    "HPC_KEY_PATH",
    "HPC_KEY_VM_PATH",
    "HPC_HOME_PATH",
    "HPC_DEFAULT_COMMAND",
    "SCP",
    "SCP_PRESERVE_TIMES",
    "MODE"
]

# HPC related constants
# Must be either gwdu101 or gwdu102 (have /scratch1 access)
# gwdu103 has no access to /scratch1 (have /scratch2 access)
HPC_HOST: str = "gwdu101.gwdg.de"
HPC_USERNAME: str = "mmustaf"
HPC_KEY_PATH: str = "/home/mm/.ssh/gwdg-cluster.pub"
HPC_KEY_VM_PATH: str = "/home/cloud/.ssh/gwdg-cluster.pub"
HPC_HOME_PATH: str = f"/home/users/{HPC_USERNAME}"
HPC_DEFAULT_COMMAND: str = f"ls -la"

# Secure copy protocol related constants
SCP = "ON"
SCP_PRESERVE_TIMES = "True"
MODE = "0755"

