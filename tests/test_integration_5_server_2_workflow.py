from os import environ
from requests import (
    get as requests_get,
    post as requests_post,
    put as requests_put
)
from operandi_utils.database import sync_db_get_workflow
from tests.helpers.asserts import assert_exists_wf_db_resource, assert_local_dir_workflow

OPERANDI_SERVER_URL = environ.get("OPERANDI_SERVER_URL")


def test_post_workflow_script(auth, bytes_template_workflow):
    # Post a new workflow script
    nf_file = {"nextflow_script": bytes_template_workflow}
    response = requests_post(url=f"{OPERANDI_SERVER_URL}/workflow", files=nf_file, auth=auth)
    assert response.status_code == 201
    wf_id = response.json()["resource_id"]

    wf_db = sync_db_get_workflow(workflow_id=wf_id)
    assert_exists_wf_db_resource(wf_db, workflow_id=wf_id)
    assert_local_dir_workflow(wf_id)


def test_put_workflow_script(auth, bytes_template_workflow, bytes_default_workflow):
    put_wf_id = "put_workflow_id"
    # The first put request creates a new workflow
    nf_file = {"nextflow_script": bytes_template_workflow},
    response = requests_put(url=f"{OPERANDI_SERVER_URL}/workflow/{put_wf_id}", files=nf_file, auth=auth)
    assert response.status_code == 201
    wf_id = response.json()["resource_id"]
    assert_local_dir_workflow(wf_id)
    wf_db = sync_db_get_workflow(workflow_id=wf_id)
    assert_exists_wf_db_resource(wf_db, workflow_id=wf_id)

    workflow_dir1 = wf_db.workflow_dir
    workflow_path1 = wf_db.workflow_script_path
    assert workflow_dir1, "Failed to extract workflow dir path 1"
    assert workflow_path1, "Failed to extract workflow path 1"

    # The second put request replaces the previously created workflow
    nf_file = {"nextflow_script": bytes_default_workflow}
    response = requests_put(url=f"{OPERANDI_SERVER_URL}/workflow/{put_wf_id}", files=nf_file, auth=auth)
    assert response.status_code == 201
    wf_id = response.json()["resource_id"]
    wf_db = sync_db_get_workflow(workflow_id=wf_id)
    assert_exists_wf_db_resource(wf_db, workflow_id=wf_id)
    assert_local_dir_workflow(wf_id)

    workflow_dir2 = wf_db.workflow_dir
    workflow_path2 = wf_db.workflow_script_path
    assert workflow_dir2, "Failed to extract workflow dir path 2"
    assert workflow_path2, "Failed to extract workflow path 2"

    assert workflow_dir1 == workflow_dir2, \
        f"Workflow dir paths should match, but does not: {workflow_dir1} != {workflow_dir2}"
    assert workflow_path1 != workflow_path2, \
        f"Workflow paths should not, but match: {workflow_path1} == {workflow_path2}"


def test_put_workflow_not_allowed(auth, bytes_template_workflow):
    production_workflow_ids = ["template_workflow", "default_workflow", "odem_workflow"]

    # Try to replace a production workflow which should raise an error code of 405
    nf_file = {"nextflow_script": bytes_template_workflow}
    for workflow_id in production_workflow_ids:
        response = requests_put(url=f"{OPERANDI_SERVER_URL}/workflow/{workflow_id}", files=nf_file, auth=auth)
        assert response.status_code == 405


# Not implemented/planned in the WebAPI
def _test_delete_workflow():
    pass


# Not implemented/planned in the WebAPI
def _test_delete_workflow_non_existing():
    pass


def test_get_workflow_script(auth, bytes_template_workflow):
    # Post a new workflow script
    nf_file = {"nextflow_script": bytes_template_workflow}
    response = requests_post(url=f"{OPERANDI_SERVER_URL}/workflow", files=nf_file, auth=auth)
    assert response.status_code == 201
    wf_id = response.json()["resource_id"]
    assert_local_dir_workflow(wf_id)

    # Get the same workflow script
    response = requests_get(url=f"{OPERANDI_SERVER_URL}/workflow/{wf_id}", auth=auth)
    assert response.status_code == 200
    print(response.headers)
    assert response.headers.get("content-disposition").find(".nf") > -1, "filename should have the '.nf' extension"


def test_get_workflow_non_existing(auth):
    non_wf_id = "non_existing_workflow_id"
    response = requests_post(url=f"{OPERANDI_SERVER_URL}/workflow/{non_wf_id}", auth=auth)
    assert response.status_code == 404


# This is already implemented as a part of the harvester full cycle test
def _test_run_operandi_workflow():
    pass


# This is already implemented as a part of the harvester full cycle test
def _test_running_workflow_job_status():
    pass
