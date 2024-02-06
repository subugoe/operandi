from tests.helpers_asserts import assert_exists_db_resource
from .helpers_asserts import (
    assert_local_dir_workflow,
    assert_response_status_code
)


def test_post_workflow_script(operandi, auth, db_workflows, bytes_template_workflow):
    # Post a new workflow script
    response = operandi.post(
        "/workflow",
        files={"nextflow_script": bytes_template_workflow},
        auth=auth
    )
    assert_response_status_code(response.status_code, expected_floor=2)
    workflow_id = response.json()['resource_id']
    assert_local_dir_workflow(workflow_id)
    db_workflow = db_workflows.find_one({"workflow_id": workflow_id})
    assert_exists_db_resource(db_workflow, resource_key="workflow_id", resource_id=workflow_id)


def test_put_workflow_script(operandi, auth, db_workflows, bytes_template_workflow, bytes_default_workflow):
    put_workflow_id = "put_workflow_id"
    # The first put request creates a new workflow
    response = operandi.put(
        f"/workflow/{put_workflow_id}",
        files={"nextflow_script": bytes_template_workflow},
        auth=auth
    )
    assert_response_status_code(response.status_code, expected_floor=2)
    workflow_id = response.json()['resource_id']
    assert_local_dir_workflow(workflow_id)
    db_workflow = db_workflows.find_one({"workflow_id": workflow_id})
    assert_exists_db_resource(db_workflow, resource_key="workflow_id", resource_id=workflow_id)

    workflow_dir1 = db_workflow["workflow_dir"]
    workflow_path1 = db_workflow["workflow_script_path"]
    assert workflow_dir1, "Failed to extract workflow dir path 1"
    assert workflow_path1, "Failed to extract workflow path 1"

    # The second put request replaces the previously created workflow
    response = operandi.put(
        f"/workflow/{put_workflow_id}",
        files={"nextflow_script": bytes_default_workflow},
        auth=auth
    )
    assert_response_status_code(response.status_code, expected_floor=2)
    workflow_id = response.json()['resource_id']
    assert_local_dir_workflow(workflow_id)
    db_workflow = db_workflows.find_one({"workflow_id": workflow_id})
    assert_exists_db_resource(db_workflow, resource_key="workflow_id", resource_id=workflow_id)

    workflow_dir2 = db_workflow["workflow_dir"]
    workflow_path2 = db_workflow["workflow_script_path"]
    assert workflow_dir2, "Failed to extract workflow dir path 2"
    assert workflow_path2, "Failed to extract workflow path 2"

    assert workflow_dir1 == workflow_dir2, \
        f"Workflow dir paths should match, but does not: {workflow_dir1} != {workflow_dir2}"
    assert workflow_path1 != workflow_path2, \
        f"Workflow paths should not, but match: {workflow_path1} == {workflow_path2}"


def test_put_workflow_not_allowed(operandi, auth, db_workflows, bytes_template_workflow):
    production_workflow_ids = [
        "template_workflow",
        "default_workflow",
        "odem_workflow"
    ]

    # Try to replace a production workflow which should raise an error code of 405
    for workflow_id in production_workflow_ids:
        response = operandi.put(
            f"/workflow/{workflow_id}",
            files={"nextflow_script": bytes_template_workflow},
            auth=auth
        )
        assert_response_status_code(response.status_code, expected_floor=4)


# Not implemented/planned in the WebAPI
def _test_delete_workflow():
    pass


# Not implemented/planned in the WebAPI
def _test_delete_workflow_non_existing():
    pass


def test_get_workflow_script(operandi, auth, bytes_template_workflow):
    # Post a new workflow script
    response = operandi.post(
        "/workflow",
        files={"nextflow_script": bytes_template_workflow},
        auth=auth
    )
    assert_response_status_code(response.status_code, expected_floor=2)
    workflow_id = response.json()['resource_id']
    assert_local_dir_workflow(workflow_id)

    # Get the same workflow script
    response = operandi.get(
        f"/workflow/{workflow_id}",
        headers={"accept": "text/vnd.ocrd.workflow"},
        auth=auth
    )
    assert_response_status_code(response.status_code, expected_floor=2)
    print(response.headers)
    assert response.headers.get('content-disposition').find(".nf") > -1, \
        "filename should have the '.nf' extension"


def test_get_workflow_non_existing(operandi, auth):
    non_workflow_id = "non_existing_workflow_id"
    response = operandi.get(
        f"/workflow/{non_workflow_id}",
        headers={"accept": "text/vnd.ocrd.workflow"},
        auth=auth
    )
    assert_response_status_code(response.status_code, expected_floor=4)


# This is already implemented as a part of the harvester full cycle test
def _test_run_operandi_workflow():
    pass


# This is already implemented as a part of the harvester full cycle test
def _test_running_workflow_job_status():
    pass
