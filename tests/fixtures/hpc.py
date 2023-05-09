from pytest import fixture
from src.utils.operandi_utils import (
    HPCExecutor,
    HPCIOTransfer
)
from tests.helpers_asserts import assert_exists_file
from tests.constants import (
    OPERANDI_HPC_HOST,
    OPERANDI_HPC_HOST_PROXY,
    OPERANDI_HPC_HOST_TRANSFER,
    OPERANDI_HPC_SSH_KEYPATH,
    OPERANDI_HPC_USERNAME
)


@fixture(scope="module", name="hpc_data_transfer")
def fixture_hpc_io_transfer_connector():
    assert_exists_file(OPERANDI_HPC_SSH_KEYPATH)
    try:
        hpc_transfer_connector = HPCIOTransfer()
        hpc_transfer_connector.connect(
            OPERANDI_HPC_HOST_TRANSFER,
            OPERANDI_HPC_USERNAME,
            OPERANDI_HPC_SSH_KEYPATH
        )
    except Exception as err:
        raise Exception(f"SSH connection to the HPC has failed: {err}")
    yield hpc_transfer_connector


@fixture(scope="module", name="hpc_command_executor")
def fixture_hpc_execution_connector():
    assert_exists_file(OPERANDI_HPC_SSH_KEYPATH)
    try:
        hpc_paramiko_connector = HPCExecutor()
        hpc_paramiko_connector.connect(
            OPERANDI_HPC_HOST,
            OPERANDI_HPC_HOST_PROXY,
            OPERANDI_HPC_USERNAME,
            OPERANDI_HPC_SSH_KEYPATH
        )
    except Exception as err:
        raise Exception(f"SSH connection to the HPC has failed: {err}")
    yield hpc_paramiko_connector
