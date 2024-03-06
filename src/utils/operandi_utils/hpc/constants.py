__all__ = [
    "HPC_EXECUTOR_HOSTS",
    "HPC_EXECUTOR_PROXY_HOSTS",
    "HPC_TRANSFER_HOSTS",
    "HPC_TRANSFER_PROXY_HOSTS",
    "SBATCH_EXE_PATH"
]

# "gwdu103.hpc.gwdg.de" - bad host entry, has no access to /scratch1, but to /scratch2
HPC_EXECUTOR_HOSTS = ["gwdu102.hpc.gwdg.de", "gwdu101.hpc.gwdg.de", "login-mdc.hpc.gwdg.de"]
HPC_EXECUTOR_PROXY_HOSTS = ["login.gwdg.de"]
HPC_TRANSFER_HOSTS = ["transfer-scc.gwdg.de", "transfer-mdc.hpc.gwdg.de"]
HPC_TRANSFER_PROXY_HOSTS = ["transfer.gwdg.de", "login.gwdg.de"]

SBATCH_EXE_PATH: str = "/usr/local/slurm/slurm/current/install/bin/sbatch"
