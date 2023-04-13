from pytest import fixture
from service_broker.hpc_connector import HPCConnector
from ..helpers_asserts import assert_exists_file
from .constants import (
    OPERANDI_HPC_HOST,
    OPERANDI_HPC_SSH_KEYPATH,
    OPERANDI_HPC_USERNAME,
)


@fixture(scope="module")
def fixture_hpc_connector():
    assert_exists_file(OPERANDI_HPC_SSH_KEYPATH)
    try:
        hpc_connector = HPCConnector()
        hpc_connector.connect_to_hpc(
            OPERANDI_HPC_HOST,
            OPERANDI_HPC_USERNAME,
            OPERANDI_HPC_SSH_KEYPATH
        )
    except Exception as err:
        raise Exception(f"SSH connection to the HPC has failed: {err}")
    yield hpc_connector
