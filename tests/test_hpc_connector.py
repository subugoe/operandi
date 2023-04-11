import os
import pytest
from service_broker.hpc_connector import HPCConnector


def test_ssh_key_file_availability(hpc_ssh_key):
    assert os.path.exists(hpc_ssh_key), f"SSH key path does not exist: {hpc_ssh_key}"
    assert os.path.isfile(hpc_ssh_key), f"SSH key path is not a file: {hpc_ssh_key}"


def test_ssh_hpc_connectivity(hpc_host, hpc_username, hpc_ssh_key):
    try:
        HPCConnector().connect_to_hpc(hpc_host, hpc_username, hpc_ssh_key)
    except Exception:
        raise "SSH connection to the HPC has failed"
