from datetime import datetime
from os import environ
from pathlib import Path
from time import sleep
from tests.helpers_asserts import assert_exists_dir, assert_exists_file
from tests.constants import BATCH_SCRIPT_EMPTY

OPERANDI_SERVER_BASE_DIR = environ.get("OPERANDI_SERVER_BASE_DIR")
current_time = datetime.now().strftime("%Y%m%d_%H%M%S%f")
ID_WORKSPACE = f"test_folder_{current_time}"

def test_hpc_connector_transfer_file(hpc_nhr_data_transfer, path_batch_script_empty):
    """
    Testing the put_file and get_file functionality of the HPC transfer
    """
    assert_exists_file(str(path_batch_script_empty))

    test_hpc_file_path = Path(hpc_nhr_data_transfer.project_root_dir_with_env, BATCH_SCRIPT_EMPTY)
    hpc_nhr_data_transfer.put_file(local_src=path_batch_script_empty, remote_dst=str(test_hpc_file_path))
    sleep(2)
    test_local_received_file_path = Path(OPERANDI_SERVER_BASE_DIR, BATCH_SCRIPT_EMPTY)
    hpc_nhr_data_transfer.get_file(remote_src=str(test_hpc_file_path), local_dst=str(test_local_received_file_path))
    sleep(2)
    assert_exists_file(str(test_local_received_file_path))


def test_hpc_connector_transfer_dir(hpc_nhr_data_transfer, path_dummy_workspace_data_dir):
    """
    Testing the put_dir and get_dir functionality of the HPC transfer
    """
    assert_exists_dir(str(path_dummy_workspace_data_dir))
    test_hpc_dir_path = Path(hpc_nhr_data_transfer.project_root_dir_with_env, ID_WORKSPACE)
    hpc_nhr_data_transfer.put_dir(local_src=str(path_dummy_workspace_data_dir), remote_dst=str(test_hpc_dir_path))
    sleep(5)
    test_local_received_dir_path = Path(OPERANDI_SERVER_BASE_DIR, ID_WORKSPACE)
    hpc_nhr_data_transfer.get_dir(remote_src=str(test_hpc_dir_path), local_dst=str(test_local_received_dir_path))
    sleep(2)
    assert_exists_dir(str(test_local_received_dir_path))
