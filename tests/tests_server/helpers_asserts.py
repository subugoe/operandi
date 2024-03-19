from os import environ
from os.path import join
from operandi_server.constants import SERVER_WORKFLOW_JOBS_ROUTER, SERVER_WORKFLOWS_ROUTER, SERVER_WORKSPACES_ROUTER
from tests.helpers_asserts import assert_exists_dir, assert_exists_not


def __resolve_local_resource_path(resource_type: str, resource_id: str) -> str:
    if resource_type not in [SERVER_WORKFLOWS_ROUTER, SERVER_WORKSPACES_ROUTER, SERVER_WORKFLOW_JOBS_ROUTER]:
        raise ValueError(f"Unknown resource type: {resource_type}")
    if not resource_id:
        raise ValueError(f"Unknown {resource_type} id")
    return join(environ.get("OPERANDI_SERVER_BASE_DIR"), resource_type, resource_id)


def assert_local_dir_workflow_job(workflow_job_id: str):
    workflow_dir = __resolve_local_resource_path(SERVER_WORKFLOW_JOBS_ROUTER, workflow_job_id)
    assert_exists_dir(workflow_dir)


def assert_local_dir_workflow_job_not(workflow_job_id: str):
    workflow_dir = __resolve_local_resource_path(SERVER_WORKFLOW_JOBS_ROUTER, workflow_job_id)
    assert_exists_not(workflow_dir)


def assert_local_dir_workflow(workflow_id: str):
    workflow_dir = __resolve_local_resource_path(SERVER_WORKFLOWS_ROUTER, workflow_id)
    assert_exists_dir(workflow_dir)


def assert_local_dir_workflow_not(workflow_id: str):
    workflow_dir = __resolve_local_resource_path(SERVER_WORKFLOWS_ROUTER, workflow_id)
    assert_exists_not(workflow_dir)


def assert_local_dir_workspace(workspace_id: str):
    workspace_dir = __resolve_local_resource_path(SERVER_WORKSPACES_ROUTER, workspace_id)
    assert_exists_dir(workspace_dir)


def assert_local_dir_workspace_not(workspace_id: str):
    workspace_dir = __resolve_local_resource_path(SERVER_WORKSPACES_ROUTER, workspace_id)
    assert_exists_not(workspace_dir)
