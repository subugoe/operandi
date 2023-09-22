from os.path import exists, isfile
from paramiko import AutoAddPolicy, SSHClient


def check_keyfile_existence(hpc_key_path: str):
    if not exists(hpc_key_path):
        raise FileNotFoundError(f"HPC key path does not exists: {hpc_key_path}")
    if not isfile(hpc_key_path):
        raise FileNotFoundError(f"HPC key path is not a file: {hpc_key_path}")


def create_ssh_connection_to_hpc(host: str, proxy_host: str, username: str, key_path: str) -> SSHClient:
    check_keyfile_existence(hpc_key_path=key_path)
    proxy_channel = create_proxy_jump(
        host=host,
        proxy_host=proxy_host,
        username=username,
        key_path=key_path
    )
    ssh_client = SSHClient()
    ssh_client.set_missing_host_key_policy(AutoAddPolicy())
    ssh_client.connect(
        hostname=host,
        username=username,
        key_filename=key_path,
        sock=proxy_channel
    )
    return ssh_client


def create_proxy_jump(host: str, proxy_host: str, username: str, key_path: str):
    jump_box = SSHClient()
    jump_box.set_missing_host_key_policy(AutoAddPolicy())
    jump_box.connect(
        proxy_host,
        username=username,
        key_filename=key_path
    )
    jump_box_channel = jump_box.get_transport().open_channel(
        kind="direct-tcpip",
        dest_addr=(host, 22),
        src_addr=(proxy_host, 22)
    )
    return jump_box_channel



