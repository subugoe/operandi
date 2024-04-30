__all__ = [
    "HPC_DIR_BATCH_SCRIPTS",
    "HPC_DIR_SLURM_WORKSPACES",
    "HPC_EXECUTOR_HOSTS",
    "HPC_EXECUTOR_PROXY_HOSTS",
    "HPC_JOB_DEADLINE_TIME_REGULAR",
    "HPC_JOB_DEADLINE_TIME_TEST",
    "HPC_PATH_HOME_USERS",
    "HPC_PATH_SCRATCH1_USERS",
    "HPC_TRANSFER_HOSTS",
    "HPC_TRANSFER_PROXY_HOSTS"
]

# "gwdu103.hpc.gwdg.de" - bad host entry, has no access to /scratch1, but to /scratch2
HPC_EXECUTOR_HOSTS = ["login-mdc.hpc.gwdg.de", "gwdu101.hpc.gwdg.de", "gwdu102.hpc.gwdg.de"]
HPC_EXECUTOR_PROXY_HOSTS = ["login.gwdg.de"]
HPC_TRANSFER_HOSTS = ["transfer-scc.gwdg.de", "transfer-mdc.hpc.gwdg.de"]
HPC_TRANSFER_PROXY_HOSTS = ["transfer.gwdg.de", "login.gwdg.de"]
HPC_PATH_HOME_USERS = "/home/users"
HPC_PATH_SCRATCH1_USERS = "/scratch1/users"
HPC_DIR_BATCH_SCRIPTS = "batch_scripts"
HPC_DIR_SLURM_WORKSPACES = "slurm_workspaces"
HPC_JOB_DEADLINE_TIME_REGULAR = "48:00:00"
HPC_JOB_DEADLINE_TIME_TEST = "1:00:00"
