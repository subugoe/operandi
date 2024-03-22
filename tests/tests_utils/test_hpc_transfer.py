from datetime import datetime
from os import environ
from os.path import join
from time import sleep
from tests.helpers_asserts import assert_exists_dir, assert_exists_file

OPERANDI_SERVER_BASE_DIR = environ.get("OPERANDI_SERVER_BASE_DIR")
BATCH_SCRIPT_ID = "test_empty.sh"

current_time = datetime.now().strftime("%Y%m%d_%H%M")
ID_WORKSPACE = f"test_folder_{current_time}"


def test_hpc_connector_transfer_file(hpc_data_transfer, path_batch_script_empty):
    """
    Testing the put_file and get_file functionality of the HPC transfer
    """
    assert_exists_file(path_batch_script_empty)

    test_hpc_file_path = join(hpc_data_transfer.project_root_dir, BATCH_SCRIPT_ID)
    hpc_data_transfer.put_file(local_src=path_batch_script_empty, remote_dst=test_hpc_file_path)
    sleep(2)
    test_local_received_file_path = join(OPERANDI_SERVER_BASE_DIR, BATCH_SCRIPT_ID)
    hpc_data_transfer.get_file(remote_src=test_hpc_file_path, local_dst=test_local_received_file_path)
    sleep(2)
    assert_exists_file(test_local_received_file_path)


def test_hpc_connector_transfer_dir(hpc_data_transfer, path_dummy_workspace_data_dir):
    """
    Testing the put_dir and get_dir functionality of the HPC transfer
    """
    assert_exists_dir(path_dummy_workspace_data_dir)
    test_hpc_dir_path = join(hpc_data_transfer.project_root_dir, ID_WORKSPACE)
    hpc_data_transfer.put_dir(local_src=path_dummy_workspace_data_dir, remote_dst=test_hpc_dir_path)
    sleep(5)
    test_local_received_dir_path = join(OPERANDI_SERVER_BASE_DIR, ID_WORKSPACE)
    hpc_data_transfer.get_dir(remote_src=test_hpc_dir_path, local_dst=test_local_received_dir_path)
    sleep(2)
    assert_exists_dir(test_local_received_dir_path)
