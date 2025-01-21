from logging import Logger
from os import environ
from os.path import join
from pathlib import Path
from typing import Optional

from paramiko import AutoAddPolicy, RSAKey, SSHClient

from .constants import HPC_NHR_CLUSTERS

SSH_RECONNECT_TRIES = 5

class NHRConnector:
    def __init__(
        self,
        logger: Logger,
        project_username: Optional[str] = environ.get("OPERANDI_HPC_PROJECT_USERNAME", None),
        project_env: Optional[str] = environ.get("OPERANDI_HPC_PROJECT_NAME", None),
        key_path: Optional[str] = environ.get("OPERANDI_HPC_SSH_KEYPATH", None),
        key_pass: Optional[str] = environ.get("OPERANDI_HPC_SSH_KEYPASS", None),
    ) -> None:
        if not project_username:
            raise ValueError("Environment variable is probably not set: OPERANDI_HPC_PROJECT_USERNAME")
        if not project_env:
            raise ValueError("Environment variable is probably not set: OPERANDI_HPC_PROJECT_NAME")
        if not key_path:
            raise ValueError("Environment variable is probably not set: OPERANDI_HPC_SSH_KEYPATH")
        self.logger = logger
        self.project_username = project_username
        self.key_path = Path(key_path)
        self.key_pass = key_pass
        self.check_keyfile_existence(key_path=self.key_path)
        self.logger.debug(f"Retrieving hpc frontend server private key file from path: {self.key_path}")
        self._ssh_client = None
        self._ssh_reconnect_tries = SSH_RECONNECT_TRIES
        self._ssh_reconnect_tries_remaining = self._ssh_reconnect_tries
        # TODO: Make the sub cluster options selectable
        self.project_root_dir: str = HPC_NHR_CLUSTERS["EmmyPhase2"]["scratch-emmy-hdd"]
        self.project_root_dir_with_env: str = join(self.project_root_dir, project_env)
        self.batch_scripts_dir: str = join(self.project_root_dir, project_env, "batch_scripts")
        self.slurm_workspaces_dir: str = join(self.project_root_dir, project_env, "slurm_workspaces")

    @property
    def ssh_client(self):
        if self._ssh_client:
            self._ssh_client.close()
            self._ssh_client = None
        self._ssh_client = self.connect_to_hpc_nhr_frontend_server(host=HPC_NHR_CLUSTERS["EmmyPhase2"]["host"])
        return self._ssh_client

    @staticmethod
    def check_keyfile_existence(key_path: Path):
        if not key_path.exists():
            raise FileNotFoundError(f"HPC private key path does not exists: {key_path}")
        if not key_path.is_file():
            raise FileNotFoundError(f"HPC private key path is not a file: {key_path}")

    def connect_to_hpc_nhr_frontend_server(self, host: str, port: int = 22) -> SSHClient:
        ssh_client = SSHClient()
        ssh_client.set_missing_host_key_policy(AutoAddPolicy())
        hpc_pkey = RSAKey.from_private_key_file(str(self.key_path), self.key_pass)
        self.logger.info(f"Connecting to hpc frontend server {host}:{port} with username: {self.project_username}")
        ssh_client.connect(
            hostname=host, port=port, username=self.project_username, pkey=hpc_pkey, passphrase=self.key_pass)
        self.logger.debug(f"Successfully connected to the hpc frontend server")
        return ssh_client
