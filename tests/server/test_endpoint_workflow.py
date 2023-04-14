from ..helpers_asserts import (
    assert_exists_db_resource,
    assert_exists_db_resource_not
)
from .helpers_asserts import (
    assert_local_dir_workflow,
    assert_local_dir_workflow_not,
    assert_response_status_code
)


def test_post_workflow_script(operandi, auth, workflow_collection, workflow1):
    # Post a new workflow script
    response = operandi.post("/workflow", files=workflow1, auth=auth)
    assert_response_status_code(response.status_code, expected_floor=2)
    workflow_id = response.json()['resource_id']
    assert_local_dir_workflow(workflow_id)
    db_workflow = workflow_collection.find_one(
        {"workflow_id": workflow_id}
    )
    assert_exists_db_resource(db_workflow, "workflow_id", workflow_id)


def test_put_workflow_script(operandi, auth, workflow_collection, workflow1, workflow2):
    put_workflow_id = "put_workflow_id"
    # The first put request creates a new workflow
    response = operandi.put(f"/workflow/{put_workflow_id}", files=workflow1, auth=auth)
    assert_response_status_code(response.status_code, expected_floor=2)
    workflow_id = response.json()['resource_id']
    assert_local_dir_workflow(workflow_id)
    db_workflow = workflow_collection.find_one(
        {"workflow_id": workflow_id}
    )
    assert_exists_db_resource(db_workflow, "workflow_id", workflow_id)

    workflow_dir_path1 = db_workflow["workflow_path"]
    workflow_path1 = db_workflow["workflow_script_path"]
    assert workflow_dir_path1, "Failed to extract workflow dir path 1"
    assert workflow_path1, "Failed to extract workflow path 1"

    # The second put request replaces the previously created workflow
    response = operandi.put(f"/workflow/{put_workflow_id}", files=workflow2, auth=auth)
    assert_response_status_code(response.status_code, expected_floor=2)
    workflow_id = response.json()['resource_id']
    assert_local_dir_workflow(workflow_id)
    db_workflow = workflow_collection.find_one(
        {"workflow_id": workflow_id}
    )
    assert_exists_db_resource(db_workflow, "workflow_id", workflow_id)

    workflow_dir_path2 = db_workflow["workflow_path"]
    workflow_path2 = db_workflow["workflow_script_path"]
    assert workflow_dir_path2, "Failed to extract workflow dir path 2"
    assert workflow_path2, "Failed to extract workflow path 2"

    assert workflow_dir_path1 == workflow_dir_path2, \
        f"Workflow dir paths should match, but does not: {workflow_dir_path1} != {workflow_dir_path2}"
    assert workflow_path1 != workflow_path2, \
        f"Workflow paths should not, but match: {workflow_path1} == {workflow_path2}"


# Not implemented/planned in the WebAPI
def _test_delete_workflow():
    pass


# Not implemented/planned in the WebAPI
def _test_delete_workflow_non_existing():
    pass


def test_get_workflow_script(operandi, auth, workflow1):
    # Post a new workflow script
    response = operandi.post("/workflow", files=workflow1, auth=auth)
    assert_response_status_code(response.status_code, expected_floor=2)
    workflow_id = response.json()['resource_id']
    assert_local_dir_workflow(workflow_id)

    # Get the same workflow script
    headers = {"accept": "text/vnd.ocrd.workflow"}
    response = operandi.get(f"/workflow/{workflow_id}", headers=headers)
    assert_response_status_code(response.status_code, expected_floor=2)
    print(response.headers)
    assert response.headers.get('content-disposition').find(".nf") > -1, \
        "filename should have the '.nf' extension"


# TODO: To be implemented
def _test_run_operandi_workflow():
    pass


# TODO: To be implemented
def _test_run_operandi_workflow_different_mets():
    pass


# TODO: To be implemented
def test_running_workflow_job_status():
    pass
