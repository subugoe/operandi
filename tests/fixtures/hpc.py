from pytest import fixture
from operandi_utils.hpc import HPCExecutor, HPCTransfer


@fixture(scope="package", name="hpc_data_transfer")
def fixture_hpc_transfer_connector():
    hpc_transfer_connector = HPCTransfer(tunel_host="localhost", tunel_port=14023)
    # print(hpc_transfer_connector.proxy_hosts)
    # print(hpc_transfer_connector.hpc_hosts)
    yield hpc_transfer_connector


@fixture(scope="package", name="hpc_command_executor")
def fixture_hpc_execution_connector():
    hpc_paramiko_connector = HPCExecutor(tunel_host="localhost", tunel_port=14022)
    # print(hpc_paramiko_connector.proxy_hosts)
    # print(hpc_paramiko_connector.hpc_hosts)
    yield hpc_paramiko_connector
