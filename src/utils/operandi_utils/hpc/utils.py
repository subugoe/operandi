from logging import Logger
from os.path import exists, isfile, join
from paramiko import AutoAddPolicy, SSHClient


def check_keyfile_existence(hpc_key_path: str):
    if not exists(hpc_key_path):
        raise FileNotFoundError(f"HPC key path does not exists: {hpc_key_path}")
    if not isfile(hpc_key_path):
        raise FileNotFoundError(f"HPC key path is not a file: {hpc_key_path}")


def create_ssh_connection_to_hpc(
    log: Logger,
    host: str,
    proxy_host: str,
    username: str,
    key_path: str
) -> SSHClient:
    check_keyfile_existence(hpc_key_path=key_path)
    ssh_client = SSHClient()
    log.debug(f"Setting missing host key policy for the ssh connection")
    ssh_client.set_missing_host_key_policy(AutoAddPolicy())
    proxy_channel = create_proxy_jump(
        log=log,
        host=host,
        proxy_host=proxy_host,
        username=username,
        key_path=key_path
    )
    log.debug(f"Opening a connection to host: {host}")
    ssh_client.connect(
        hostname=host,
        username=username,
        key_filename=key_path,
        sock=proxy_channel,
        auth_timeout=60,
        banner_timeout=60,
        timeout=120
    )
    log.debug(f"Successfully opened a host connection")
    return ssh_client


def create_proxy_jump(
    log: Logger,
    username: str,
    key_path: str,
    host: str,
    proxy_host: str,
    host_port: int = 22,
    proxy_host_port: int = 22,
    channel_kind: str = "direct-tcpip",
    auth_timeout: float = 60,
    banner_timeout: float = 60,
    connection_timeout: float = 120,
    channel_timeout: float = 120
):
    jump_box = SSHClient()
    log.debug(f"Setting missing host key policy for the ssh jump connection")
    jump_box.set_missing_host_key_policy(AutoAddPolicy())
    log.debug(f"Opening a connection to proxy host: {proxy_host}")
    jump_box.connect(
        proxy_host,
        username=username,
        key_filename=key_path,
        timeout=connection_timeout,
        auth_timeout=auth_timeout,
        banner_timeout=banner_timeout,
        channel_timeout=channel_timeout
    )
    log.debug(f"Successfully opened a proxy host connection")
    log.debug(f"""
        Opening a channel: {channel_kind}, 
        from proxy host: {proxy_host}:{proxy_host_port}, 
        to host: {host}:{host_port}
    """)
    jump_box_channel = jump_box.get_transport().open_channel(
        kind=channel_kind,
        dest_addr=(host, host_port),
        src_addr=(proxy_host, proxy_host_port),
        timeout=channel_timeout
    )
    log.debug(f"Successfully opened a channel from proxy host to host")
    return jump_box_channel


def resolve_hpc_user_home_dir(username: str) -> str:
    return f"/home/users/{username}"


def resolve_hpc_user_scratch_dir(username: str) -> str:
    return f"/scratch1/users/{username}"


def resolve_hpc_project_root_dir(username: str, project_root_dir: str) -> str:
    return join(resolve_hpc_user_scratch_dir(username), project_root_dir)


def resolve_hpc_batch_scripts_dir(username: str, project_root_dir: str) -> str:
    return join(resolve_hpc_project_root_dir(username, project_root_dir), "batch_scripts")


def resolve_hpc_slurm_workspaces_dir(username: str, project_root_dir: str) -> str:
    return join(resolve_hpc_project_root_dir(username, project_root_dir), "slurm_workspaces")
