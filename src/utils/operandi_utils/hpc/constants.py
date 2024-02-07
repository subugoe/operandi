__all__ = [
    "HPC_EXECUTOR_HOST",
    "HPC_EXECUTOR_PROXY_HOST",
    "HPC_TRANSFER_HOST",
    "HPC_TRANSFER_PROXY_HOST"
]

# TODO: Pass multiple hosts. When a host timeouts, another host should be tried
HPC_EXECUTOR_HOST = "gwdu101.hpc.gwdg.de"  # "login-mdc.hpc.gwdg.de"
HPC_EXECUTOR_PROXY_HOST = "login.gwdg.de"
HPC_TRANSFER_HOST = "transfer-scc.gwdg.de"
HPC_TRANSFER_PROXY_HOST = "login.gwdg.de"  # "transfer.gwdg.de"
