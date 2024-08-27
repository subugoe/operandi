from pytest import fixture
from operandi_utils.hpc import NHRExecutor, NHRTransfer

@fixture(scope="package", name="hpc_nhr_data_transfer")
def fixture_hpc_nhr_transfer_connector():
    hpc_transfer_connector = NHRTransfer()
    yield hpc_transfer_connector


@fixture(scope="package", name="hpc_nhr_command_executor")
def fixture_hpc_nhr_execution_connector():
    hpc_paramiko_connector = NHRExecutor()
    yield hpc_paramiko_connector
