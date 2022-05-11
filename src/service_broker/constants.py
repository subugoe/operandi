__all__ = [
    "SERVICE_BROKER_IP",
    "SERVICE_BROKER_PORT",
    "SERVICE_BROKER_PATH",
    "HPC_IP",
    "HPC_USERNAME",
    "HPC_KEY_PATH"
]

SERVICE_BROKER_IP: str = "localhost"
SERVICE_BROKER_PORT: int = 27072
SERVICE_BROKER_PATH: str = f"http://{SERVICE_BROKER_IP}:{SERVICE_BROKER_PORT}"

HPC_IP: str = "gwdu101.gwdg.de"
HPC_USERNAME: str = "mmustaf"
HPC_KEY_PATH: str = "/home/mm/.ssh/gwdg-cluster.pub"
