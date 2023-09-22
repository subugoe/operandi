from datetime import datetime
from os.path import join
from time import sleep
from tests.constants import (
    OPERANDI_SERVER_BASE_DIR,
    OPERANDI_TESTS_LOCAL_DIR_WORKSPACES,
    OPERANDI_HPC_DIR_PROJECT
)
from tests.helpers_asserts import assert_exists_dir, assert_exists_file
from tests.helpers_utils import to_asset_path


def test_hpc_connector_transfer_file(hpc_data_transfer):
    """
    Testing the put_file and get_file functionality of the HPC transfer
    """
    batch_script_id = "test_empty.sh"
    test_local_file_path = to_asset_path(resource_type='batch_scripts', name=batch_script_id)
    assert_exists_file(test_local_file_path)

    test_hpc_file_path = join(OPERANDI_HPC_DIR_PROJECT, batch_script_id)
    hpc_data_transfer.put_file(
        local_src=test_local_file_path,
        remote_dst=test_hpc_file_path
    )

    sleep(1)

    test_local_received_file_path = join(OPERANDI_SERVER_BASE_DIR, batch_script_id)
    hpc_data_transfer.get_file(
        remote_src=test_hpc_file_path,
        local_dst=test_local_received_file_path
    )
    assert_exists_file(test_local_received_file_path)


def test_hpc_connector_transfer_dir(hpc_data_transfer):
    """
    Testing the put_dir and get_dir functionality of the HPC transfer
    """
    test_local_dir_path = join(to_asset_path(resource_type="workspaces", name="dummy_ws"), "data")
    assert_exists_dir(test_local_dir_path)

    current_time = datetime.now().strftime("%Y%m%d_%H%M")
    workspace_id = f"test_workspace_{current_time}"
    test_hpc_dir_path = join(OPERANDI_HPC_DIR_PROJECT, workspace_id)
    hpc_data_transfer.put_dir(
        local_src=test_local_dir_path,
        remote_dst=test_hpc_dir_path
    )

    sleep(3)

    test_local_received_dir_path = join(OPERANDI_TESTS_LOCAL_DIR_WORKSPACES, workspace_id)
    hpc_data_transfer.get_dir(
        remote_src=test_hpc_dir_path,
        local_dst=test_local_received_dir_path
    )
    assert_exists_dir(test_local_received_dir_path)
