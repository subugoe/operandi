from os import environ
from pathlib import Path
import pytest
from service_broker.hpc_connector import HPCConnector


@pytest.fixture(scope="session", name="hpc_host")
def _fixture_hpc_host():
    yield environ.get("OPERANDI_HPC_HOST", "gwdu101.gwdg.de")


@pytest.fixture(scope="session", name="hpc_ssh_key")
def _fixture_hpc_ssh_key():
    yield environ.get("OPERANDI_HPC_SSH_KEYPATH", f"{Path.home()}/.ssh/gwdg-cluster.pub")


@pytest.fixture(scope="session", name="hpc_username")
def _fixture_hpc_username():
    yield environ.get("OPERANDI_HPC_USERNAME", "mmustaf")


@pytest.fixture(scope="session", name="hpc_connector")
def _fixture_hpc_connector(hpc_host, hpc_username, hpc_ssh_key):
    try:
        hpc_connector = HPCConnector()
        hpc_connector.connect_to_hpc(hpc_host, hpc_username, hpc_ssh_key)
    except Exception:
        raise "SSH connection to the HPC has failed"
    yield hpc_connector
