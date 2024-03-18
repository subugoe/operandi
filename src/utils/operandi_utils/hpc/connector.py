from logging import getLogger, Logger
from os.path import exists, isfile
from paramiko import AutoAddPolicy, Channel, RSAKey, SFTPClient, SSHClient, Transport
from pathlib import Path
from typing import List, Union

from .utils import (
    resolve_hpc_user_home_dir,
    resolve_hpc_user_scratch_dir,
    resolve_hpc_project_root_dir,
    resolve_hpc_batch_scripts_dir,
    resolve_hpc_slurm_workspaces_dir,
)


class HPCConnector:
    def __init__(
        self,
        hpc_hosts: List[str],
        proxy_hosts: List[str],
        username: str,
        key_path: Path,
        key_pass: Union[str, None],
        project_name: str,
        log: Logger = getLogger("operandi_utils.hpc.connector"),
        channel_keep_alive_interval: int = 30,
        channel_timeout: float = 180,
        connection_keep_alive_interval: int = 30,
        connection_timeout: float = 180,
        all_connections_try_times: int = 1
    ) -> None:
        self.log = log
        self.username = username

        self.verify_pkey_file_existence(key_path)

        # Use the same private key for both the proxy and hpc connections
        self.proxy_key_path = key_path
        self.proxy_key_pass = key_pass
        self.hpc_key_path = key_path
        self.hpc_key_pass = key_pass

        self.connection_keep_alive_interval = connection_keep_alive_interval
        self.connection_timeout = connection_timeout
        self.channel_keep_alive_interval = channel_keep_alive_interval
        self.channel_timeout = channel_timeout

        # A list of hpc hosts - tries to connect to all until one is successful
        self.hpc_hosts = hpc_hosts
        self.last_used_hpc_host = None

        # A list of proxy hosts - tries to connect to all until one is successful
        self.proxy_hosts = proxy_hosts
        self.last_used_proxy_host = None

        self.ssh_proxy_client = None
        self.proxy_tunnel = None
        self.ssh_hpc_client = None
        self.sftp_client = None

        self.log.info(f"""
            HPCConnector initialized with:\n
            Username: {self.username}\n
            HPC hosts: {self.hpc_hosts}\n
            Private key for hpc hosts: {self.hpc_key_path}\n
            Proxy hosts: {self.proxy_hosts}\n
            Private key for proxy hosts: {self.proxy_key_path}\n
            """)

        self.project_name = project_name
        self.user_home_dir = resolve_hpc_user_home_dir(username)
        self.user_scratch_dir = resolve_hpc_user_scratch_dir(username)
        self.project_root_dir = resolve_hpc_project_root_dir(username, project_name)
        self.batch_scripts_dir = resolve_hpc_batch_scripts_dir(username, project_name)
        self.slurm_workspaces_dir = resolve_hpc_slurm_workspaces_dir(username, project_name)

        self.log.info(f"""
            Project name: {self.project_name}\n
            User home dir: {self.user_home_dir}\n
            User scratch dir: {self.user_scratch_dir}\n
            Project root dir: {self.project_root_dir}\n
            Batch scripts root dir: {self.batch_scripts_dir}\n
            Slurm workspaces root dir: {self.slurm_workspaces_dir}\n
            """)

        self.create_ssh_connection_to_hpc_by_iteration(try_times=all_connections_try_times)

    @staticmethod
    def verify_pkey_file_existence(key_path: Path):
        if not exists(key_path):
            raise FileNotFoundError(f"Private key path does not exist: {key_path}")
        if not isfile(key_path):
            raise FileNotFoundError(f"Private key path is not a file: {key_path}")

    def connect_to_proxy_server(self, host: str, port: int = 22) -> SSHClient:
        self.ssh_proxy_client = SSHClient()
        self.log.debug(f"Setting missing host key policy for the proxy client")
        self.ssh_proxy_client.set_missing_host_key_policy(AutoAddPolicy())
        self.log.debug(f"Retrieving proxy server private key file from path: {self.proxy_key_path}")
        proxy_pkey = RSAKey.from_private_key_file(str(self.proxy_key_path), self.proxy_key_pass)
        self.log.debug(f"Connecting to proxy server {host}:{port} with username: {self.username}")
        self.ssh_proxy_client.connect(
            hostname=host,
            port=port,
            username=self.username,
            pkey=proxy_pkey,
            passphrase=self.proxy_key_pass,
            timeout=self.connection_timeout
        )
        # self.ssh_proxy_client.get_transport().set_keepalive(self.connection_keep_alive_interval)
        self.last_used_proxy_host = host
        self.log.debug(f"Successfully connected to the proxy server")
        return self.ssh_proxy_client

    def establish_proxy_tunnel(
        self,
        dst_host: str,
        dst_port: int = 22,
        src_host: str = 'localhost',
        src_port: int = 4022,
        channel_kind: str = 'direct-tcpip',
    ) -> Channel:
        proxy_transport = self.ssh_proxy_client.get_transport()
        self.log.debug(f"Configuring a tunnel to destination: {dst_host}:{dst_port}")
        self.proxy_tunnel = proxy_transport.open_channel(
            kind=channel_kind,
            src_addr=(src_host, src_port),
            dest_addr=(dst_host, dst_port),
            timeout=self.channel_timeout
        )
        # self.proxy_tunnel.get_transport().set_keepalive(self.channel_keep_alive_interval)
        self.last_used_hpc_host = dst_host
        self.log.debug(f"Successfully configured a proxy tunnel")
        return self.proxy_tunnel

    def connect_to_hpc_frontend_server(self, host: str, port: int = 22, proxy_tunnel: Channel = None) -> SSHClient:
        self.ssh_hpc_client = SSHClient()
        self.log.debug(f"Setting missing host key policy for the hpc frontend client")
        self.ssh_hpc_client.set_missing_host_key_policy(AutoAddPolicy())
        self.log.debug(f"Retrieving hpc frontend server private key file from path: {self.hpc_key_path}")
        hpc_pkey = RSAKey.from_private_key_file(str(self.hpc_key_path), self.hpc_key_pass)
        self.log.debug(f"Connecting to hpc frontend server {host}:{port} with username: {self.username}")
        self.ssh_hpc_client.connect(
            hostname=host,
            port=port,
            username=self.username,
            pkey=hpc_pkey,
            passphrase=self.hpc_key_pass,
            sock=proxy_tunnel,
            timeout=self.connection_timeout
        )
        # self.ssh_hpc_client.get_transport().set_keepalive(self.connection_keep_alive_interval)
        self.last_used_hpc_host = host
        self.log.debug(f"Successfully connected to the hpc frontend server")
        return self.ssh_hpc_client

    def create_sftp_client(self) -> SFTPClient:
        self.sftp_client = self.ssh_hpc_client.open_sftp()
        # self.sftp_client.get_channel().get_transport().set_keepalive(self.channel_keep_alive_interval)
        return self.sftp_client

    @staticmethod
    def is_transport_responsive(transport: Transport) -> bool:
        if not transport:
            return False
        if not transport.is_active():
            return False
        try:
            # Sometimes is_active() returns false-positives, hence the extra check
            transport.send_ignore()
            # Nevertheless this still returns false-positives...!!!
            # https://github.com/paramiko/paramiko/issues/2026
            return True
        except EOFError:
            return False

    def is_ssh_connection_still_responsive(self, ssh_client: SSHClient) -> bool:
        self.log.debug("Checking SSH connection responsiveness")
        if not ssh_client:
            return False
        transport = ssh_client.get_transport()
        return self.is_transport_responsive(transport)

    def is_proxy_tunnel_still_responsive(self) -> bool:
        self.log.debug("Checking proxy tunel responsiveness")
        if not self.proxy_tunnel:
            return False
        transport = self.proxy_tunnel.get_transport()
        return self.is_transport_responsive(transport)

    def is_sftp_still_responsive(self) -> bool:
        self.log.debug("Checking SFTP connection responsiveness")
        if not self.sftp_client:
            return False
        channel = self.sftp_client.get_channel()
        if not channel:
            return False
        transport = channel.get_transport()
        return self.is_transport_responsive(transport)

    def reconnect_if_required(
        self,
        hpc_host: str = None,
        hpc_port: int = 22,
        proxy_host: str = None,
        proxy_port: int = 22
    ) -> None:
        if not hpc_host:
            hpc_host = self.last_used_hpc_host
        if not proxy_host:
            proxy_host = self.last_used_proxy_host

        if not self.is_ssh_connection_still_responsive(self.ssh_proxy_client):
            self.log.warning("The connection to proxy server is not responsive, trying to open a new connection")
            self.ssh_proxy_client = self.connect_to_proxy_server(host=proxy_host, port=proxy_port)
        if not self.is_proxy_tunnel_still_responsive():
            self.log.warning("The proxy tunnel is not responsive, trying to establish a new proxy tunnel")
            self.proxy_tunnel = self.establish_proxy_tunnel(dst_host=hpc_host, dst_port=hpc_port)
        if not self.is_ssh_connection_still_responsive(self.ssh_hpc_client):
            self.log.warning("The connection to hpc frontend server is not responsive, trying to open a new connection")
            self.ssh_hpc_client = self.connect_to_hpc_frontend_server(proxy_host, proxy_port, self.proxy_tunnel)

    def recreate_sftp_if_required(
        self,
        hpc_host: str = None,
        hpc_port: int = 22,
        proxy_host: str = None,
        proxy_port: int = 22
    ) -> None:
        if not hpc_host:
            hpc_host = self.last_used_hpc_host
        if not proxy_host:
            proxy_host = self.last_used_proxy_host
        self.reconnect_if_required(
            hpc_host=hpc_host, hpc_port=hpc_port,
            proxy_host=proxy_host, proxy_port=proxy_port
        )
        if not self.is_sftp_still_responsive():
            self.log.warning("The SFTP client is not responsive, trying to create a new SFTP client")
            self.create_sftp_client()

    def create_ssh_connection_to_hpc_by_iteration(self, try_times: int = 3) -> None:
        while try_times > 0:
            for proxy_host in self.proxy_hosts:
                self.ssh_proxy_client = None
                self.last_used_proxy_host = None
                for hpc_host in self.hpc_hosts:
                    self.ssh_hpc_client = None
                    self.last_used_hpc_host = None
                    try:
                        self.reconnect_if_required(hpc_host=hpc_host, proxy_host=proxy_host)
                        return  # all connections were successful
                    except Exception as error:
                        self.log.error(f"""
                            Failed to connect to hpc host: {hpc_host}\n 
                            Over proxy host: {proxy_host}\n
                            Exception Error: {error}\n
                        """)
                        continue
            try_times -= 1

        raise Exception(f"""
            Failed to establish connection to any of the HPC hosts: {self.hpc_hosts}\n
            Using the hpc private key: {self.hpc_key_path}\n
            Over any of the proxy hosts: {self.proxy_hosts}\n
            Using the proxy private key: {self.proxy_key_path}\n
            Performed connection iterations: {try_times}\n
        """)
