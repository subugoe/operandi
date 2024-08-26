from logging import Logger
from os import environ
from os.path import join
from pathlib import Path
from typing import Optional

from paramiko import AutoAddPolicy, RSAKey, SSHClient

from .constants import HPC_NHR_CLUSTERS

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
        self._sftp_client = None
        # TODO: Make the sub cluster options selectable
        self.project_root_dir = join(HPC_NHR_CLUSTERS["EmmyPhase3"]["scratch-emmy-hdd"], project_env)
        self.slurm_workspaces_dir = join(self.project_root_dir, "slurm_workspaces")

    @property
    def ssh_client(self):
        if not self._ssh_client:
            # TODO: Make the sub cluster option selectable
            self._ssh_client = self.connect_to_hpc_nhr_frontend_server(host=HPC_NHR_CLUSTERS["EmmyPhase3"]["host"])
            # self._ssh_client.get_transport().set_keepalive(30)
        return self._ssh_client

    @staticmethod
    def check_keyfile_existence(key_path: Path):
        if not key_path.exists():
            raise FileNotFoundError(f"HPC private key path does not exists: {key_path}")
        if not key_path.is_file():
            raise FileNotFoundError(f"HPC private key path is not a file: {key_path}")

    def connect_to_hpc_nhr_frontend_server(self, host: str, port: int = 22) -> SSHClient:
        self._ssh_client = SSHClient()
        self.ssh_client.set_missing_host_key_policy(AutoAddPolicy())
        hpc_pkey = RSAKey.from_private_key_file(str(self.key_path), self.key_pass)
        self.logger.info(f"Connecting to hpc frontend server {host}:{port} with username: {self.project_username}")
        self.ssh_client.connect(
            hostname=host, port=port, username=self.project_username, pkey=hpc_pkey, passphrase=self.key_pass)
        self.logger.debug(f"Successfully connected to the hpc frontend server")
        return self.ssh_client
