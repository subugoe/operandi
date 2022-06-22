__all__ = [
  "SERVICE_BROKER_HOST",
  "SERVICE_BROKER_PORT",
  "SERVICE_BROKER_PATH",
  "HPC_HOST",
  "HPC_USERNAME",
  "HPC_KEY_PATH",
  "HPC_HOME_PATH",
  "SCP",
  "SCP_PRESERVE_TIMES",
  "MODE"
]

# Service broker related constants
SERVICE_BROKER_HOST: str = "localhost"
SERVICE_BROKER_PORT: int = 27072
SERVICE_BROKER_PATH: str = f"http://{SERVICE_BROKER_HOST}:{SERVICE_BROKER_PORT}"

# HPC related constants
HPC_HOST: str = "gwdu101.gwdg.de"
HPC_USERNAME: str = "mmustaf"
HPC_KEY_PATH: str = "/home/cloud/.ssh/gwdg-cluster.pub"
HPC_HOME_PATH: str = f"/home/users/{HPC_USERNAME}"

# Secure copy protocol related constants
SCP = "ON"
SCP_PRESERVE_TIMES = "True"
MODE = "0755"

