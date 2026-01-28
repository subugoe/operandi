from logging import StreamHandler, DEBUG
from pytest import fixture
from sys import stdout
from operandi_utils.hpc import NHRExecutor, NHRTransfer

@fixture(scope="package", name="hpc_nhr_data_transfer")
def fixture_hpc_nhr_transfer_connector():
    hpc_transfer_connector = NHRTransfer()
    hpc_transfer_connector.logger.addHandler(StreamHandler(stdout))
    hpc_transfer_connector.logger.setLevel(DEBUG)
    yield hpc_transfer_connector


@fixture(scope="package", name="hpc_nhr_command_executor")
def fixture_hpc_nhr_execution_connector():
    hpc_paramiko_connector = NHRExecutor()
    hpc_paramiko_connector.logger.addHandler(StreamHandler(stdout))
    hpc_paramiko_connector.logger.setLevel(DEBUG)
    yield hpc_paramiko_connector
