from pytest import fixture
from operandi_utils.hpc import (
    HPCExecutor,
    HPCTransfer
)
from tests.helpers_asserts import assert_exists_file
from tests.constants import (
    OPERANDI_HPC_HOST,
    OPERANDI_HPC_HOST_PROXY,
    OPERANDI_HPC_HOST_TRANSFER,
    OPERANDI_HPC_HOST_TRANSFER_PROXY,
    OPERANDI_HPC_SSH_KEYPATH,
    OPERANDI_HPC_USERNAME
)


@fixture(scope="module", name="hpc_data_transfer")
def fixture_hpc_transfer_connector():
    assert_exists_file(OPERANDI_HPC_SSH_KEYPATH)
    try:
        hpc_transfer_connector = HPCTransfer()
        hpc_transfer_connector.connect(
            host=OPERANDI_HPC_HOST_TRANSFER,
            proxy_host=OPERANDI_HPC_HOST_TRANSFER_PROXY,
            username=OPERANDI_HPC_USERNAME,
            key_path=OPERANDI_HPC_SSH_KEYPATH
        )
    except Exception as err:
        raise Exception(f"SSH connection to '{OPERANDI_HPC_HOST_TRANSFER}' "
                        f"through proxy '{OPERANDI_HPC_HOST_TRANSFER_PROXY}' has failed: {err}")
    yield hpc_transfer_connector


@fixture(scope="module", name="hpc_command_executor")
def fixture_hpc_execution_connector():
    assert_exists_file(OPERANDI_HPC_SSH_KEYPATH)
    try:
        hpc_paramiko_connector = HPCExecutor()
        hpc_paramiko_connector.connect(
            host=OPERANDI_HPC_HOST,
            proxy_host=OPERANDI_HPC_HOST_PROXY,
            username=OPERANDI_HPC_USERNAME,
            key_path=OPERANDI_HPC_SSH_KEYPATH
        )
    except Exception as err:
        raise Exception(f"SSH connection to '{OPERANDI_HPC_HOST}' "
                        f"through proxy '{OPERANDI_HPC_HOST_PROXY}' has failed: {err}")
    yield hpc_paramiko_connector
