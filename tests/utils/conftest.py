from pytest import fixture
from src.utils.operandi_utils import HPCConnector
from tests.helpers_asserts import assert_exists_file
from tests.utils.constants import (
    OPERANDI_HPC_HOST,
    OPERANDI_HPC_HOST_PROXY,
    OPERANDI_HPC_HOST_TRANSFER,
    OPERANDI_HPC_SSH_KEYPATH,
    OPERANDI_HPC_USERNAME,
    OPERANDI_HPC_HOME_PATH
)


@fixture(scope="module")
def fixture_hpc_io_transfer_connector():
    assert_exists_file(OPERANDI_HPC_SSH_KEYPATH)
    try:
        hpc_transfer_connector = HPCConnector(
            hpc_home_path=OPERANDI_HPC_HOME_PATH
        )
        hpc_transfer_connector.connect_to_hpc_io_transfer(
            OPERANDI_HPC_HOST_TRANSFER,
            OPERANDI_HPC_USERNAME,
            OPERANDI_HPC_SSH_KEYPATH
        )
    except Exception as err:
        raise Exception(f"SSH connection to the HPC has failed: {err}")
    yield hpc_transfer_connector


@fixture(scope="module")
def fixture_hpc_paramiko_connector():
    assert_exists_file(OPERANDI_HPC_SSH_KEYPATH)
    try:
        hpc_paramiko_connector = HPCConnector(
            hpc_home_path=OPERANDI_HPC_HOME_PATH
        )
        hpc_paramiko_connector.connect_to_hpc(
            OPERANDI_HPC_HOST,
            OPERANDI_HPC_HOST_PROXY,
            OPERANDI_HPC_USERNAME,
            OPERANDI_HPC_SSH_KEYPATH
        )
    except Exception as err:
        raise Exception(f"SSH connection to the HPC has failed: {err}")
    yield hpc_paramiko_connector
