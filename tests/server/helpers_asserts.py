from os.path import join
from tests.constants import (
    OPERANDI_TESTS_LOCAL_DIR_WORKFLOW_JOBS,
    OPERANDI_TESTS_LOCAL_DIR_WORKFLOWS,
    OPERANDI_TESTS_LOCAL_DIR_WORKSPACES
)
from tests.helpers_asserts import assert_exists_dir, assert_exists_not


def __resolver_resource_path(resource_type: str, resource_id: str) -> str:
    if resource_type not in ["workflow", "workspace", "workflow_job"]:
        raise ValueError(f"Unknown resource type: {resource_type}")
    if not resource_id:
        raise ValueError(f"Unknown {resource_type} id")

    if resource_type == "workflow_job":
        return join(OPERANDI_TESTS_LOCAL_DIR_WORKFLOW_JOBS, resource_id)
    if resource_type == "workflow":
        return join(OPERANDI_TESTS_LOCAL_DIR_WORKFLOWS, resource_id)
    if resource_type == "workspace":
        return join(OPERANDI_TESTS_LOCAL_DIR_WORKSPACES, resource_id)


def assert_local_dir_workflow(workflow_id: str):
    workflow_dir = __resolver_resource_path("workflow", workflow_id)
    assert_exists_dir(workflow_dir)


def assert_local_dir_workflow_not(workflow_id: str):
    workflow_dir = __resolver_resource_path("workflow", workflow_id)
    assert_exists_not(workflow_dir)


def assert_local_dir_workspace(workspace_id: str):
    workspace_dir = __resolver_resource_path("workspace", workspace_id)
    assert_exists_dir(workspace_dir)


def assert_local_dir_workspace_not(workspace_id: str):
    workspace_dir = __resolver_resource_path("workspace", workspace_id)
    assert_exists_not(workspace_dir)


def assert_response_status_code(status_code, expected_floor):
    status_floor = status_code // 100
    assert expected_floor == status_floor, \
        f"Response status code expected:{expected_floor}xx, got: {status_code}"
