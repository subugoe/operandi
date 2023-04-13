from ..constants import OPERANDI_TESTS_DIR
from ..helpers_asserts import assert_exists_dir


def assert_local_dir_workspace(workspace_id: str):
    workspace_dir = f"{OPERANDI_TESTS_DIR}/workspaces/{workspace_id}"
    assert_exists_dir(workspace_dir)


def assert_local_dir_workflow(workflow_id: str):
    workflow_dir = f"{OPERANDI_TESTS_DIR}/workflows/{workflow_id}"
    assert_exists_dir(workflow_dir)


def assert_response_status_code(status_code, expected_floor):
    status_floor = status_code // 100
    assert expected_floor == status_floor, \
        f"Response status code expected:{expected_floor}xx, got: {status_code}"
