import os
from service_broker.hpc_connector import HPCConnector
from ..conftest import OPERANDI_TESTS_DIR
from ..utils_test import to_asset_path


def test_hpc_connector_ssh_key_file_availability(hpc_ssh_key):
    assert os.path.exists(hpc_ssh_key), f"SSH key path does not exist: {hpc_ssh_key}"
    assert os.path.isfile(hpc_ssh_key), f"SSH key path is not a file: {hpc_ssh_key}"


def test_hpc_connector_ssh_connectivity(hpc_host, hpc_username, hpc_ssh_key):
    try:
        HPCConnector().connect_to_hpc(hpc_host, hpc_username, hpc_ssh_key)
    except Exception as err:
        raise "SSH connection to the HPC has failed"


def test_hpc_connector_put_directory(hpc_connector, hpc_home_path):
    dir_src = to_asset_path('workspaces/dummy_ws/')
    dir_dest = f"{hpc_home_path}/tests/dummy_ws"
    hpc_connector.put_directory(source=dir_src, destination=dir_dest)


def test_hpc_connector_get_directory(hpc_connector, hpc_home_path):
    dir_src = f"{hpc_home_path}/tests/dummy_ws"
    dir_dest = f"{OPERANDI_TESTS_DIR}/"
    hpc_connector.get_directory(source=dir_src, destination=dir_dest)
    assert os.path.exists(dir_dest), f"Expected path nonexistent: {dir_dest}"
    assert os.path.isdir(dir_dest), f"Expected path not dir: {dir_dest}"
