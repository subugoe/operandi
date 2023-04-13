from ..constants import OPERANDI_TESTS_DIR
from ..helpers_asserts import assert_exists_dir
from ..helpers_utils import to_asset_path
from .constants import OPERANDI_HPC_HOME_PATH


def test_hpc_connector_put_directory(fixture_hpc_connector):
    dir_src = to_asset_path('workspaces', 'dummy_ws/')
    dir_dest = f"{OPERANDI_HPC_HOME_PATH}/tests/dummy_ws"
    fixture_hpc_connector.put_directory(source=dir_src, destination=dir_dest)


def test_hpc_connector_get_directory(fixture_hpc_connector):
    dir_src = f"{OPERANDI_HPC_HOME_PATH}/tests/dummy_ws"
    dir_dest = f"{OPERANDI_TESTS_DIR}/workspaces/dummy_ws"
    fixture_hpc_connector.get_directory(source=dir_src, destination=dir_dest)
    assert_exists_dir(dir_dest)
