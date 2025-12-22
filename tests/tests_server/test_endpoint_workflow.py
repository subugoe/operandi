from io import BytesIO
from pytest import mark
from tests.helpers_asserts import assert_exists_db_resource
from tests.constants import WORKFLOW_DUMMY_TEXT
from .helpers_asserts import assert_local_dir_workflow, assert_response_status_code


@mark.asyncio
async def test_post_workflow_script(operandi, auth, db_workflows, bytes_template_workflow):
    # Post a new workflow script
    wf_detail = "Test template workflow with mets server"
    response = await operandi.post(
        url=f"/workflow?details={wf_detail}", files={"nextflow_script": bytes_template_workflow}, auth=auth)
    assert_response_status_code(response.status_code, expected_floor=2)
    workflow_id = response.json()['resource_id']
    assert_local_dir_workflow(workflow_id)
    db_workflow = db_workflows.find_one({"workflow_id": workflow_id})
    assert_exists_db_resource(db_workflow, resource_key="workflow_id", resource_id=workflow_id)
    assert db_workflow["details"] == wf_detail
    assert db_workflow["uses_mets_server"] == False


@mark.asyncio
async def _test_post_workflow_script_with_ms(operandi, auth, db_workflows, bytes_template_workflow_with_ms):
    # Post a new workflow script
    wf_detail = "Test template workflow with mets server"
    response = await operandi.post(
        url=f"/workflow?details={wf_detail}", files={"nextflow_script": bytes_template_workflow_with_ms}, auth=auth)
    assert_response_status_code(response.status_code, expected_floor=2)
    workflow_id = response.json()['resource_id']
    assert_local_dir_workflow(workflow_id)
    db_workflow = db_workflows.find_one({"workflow_id": workflow_id})
    assert_exists_db_resource(db_workflow, resource_key="workflow_id", resource_id=workflow_id)
    assert db_workflow["details"] == wf_detail
    assert db_workflow["uses_mets_server"] == True


@mark.asyncio
async def _test_put_workflow_script(
    operandi, auth, db_workflows, bytes_template_workflow_with_ms, bytes_default_workflow_with_ms
):
    put_workflow_id = "put_workflow_id"
    # The first put request creates a new workflow
    files = {"nextflow_script": bytes_template_workflow_with_ms}
    wf_detail = "Test template workflow with mets server"
    response = await operandi.put(url=f"/workflow/{put_workflow_id}?details={wf_detail}", files=files, auth=auth)
    assert_response_status_code(response.status_code, expected_floor=2)
    workflow_id = response.json()['resource_id']
    assert_local_dir_workflow(workflow_id)
    db_workflow = db_workflows.find_one({"workflow_id": workflow_id})
    assert_exists_db_resource(db_workflow, resource_key="workflow_id", resource_id=workflow_id)

    workflow_dir1 = db_workflow["workflow_dir"]
    workflow_path1 = db_workflow["workflow_script_path"]
    workflow_details1 = db_workflow["details"]
    assert workflow_dir1, "Failed to extract workflow dir path 1"
    assert workflow_path1, "Failed to extract workflow path 1"
    assert workflow_details1, "Failed to extract workflow details 1"
    assert db_workflow["details"] == wf_detail
    assert db_workflow["uses_mets_server"] == True

    # The second put request replaces the previously created workflow
    files = {"nextflow_script": bytes_default_workflow_with_ms}
    wf_detail_put = "Test default workflow with mets server"
    response = await operandi.put(url=f"/workflow/{put_workflow_id}?details={wf_detail_put}", files=files, auth=auth)
    assert_response_status_code(response.status_code, expected_floor=2)
    workflow_id = response.json()['resource_id']
    assert_local_dir_workflow(workflow_id)
    db_workflow = db_workflows.find_one({"workflow_id": workflow_id})
    assert_exists_db_resource(db_workflow, resource_key="workflow_id", resource_id=workflow_id)

    workflow_dir2 = db_workflow["workflow_dir"]
    workflow_path2 = db_workflow["workflow_script_path"]
    workflow_details2 = db_workflow["details"]
    assert workflow_dir2, "Failed to extract workflow dir path 2"
    assert workflow_path2, "Failed to extract workflow path 2"
    assert workflow_details2, "Failed to extract workflow details 2"
    assert db_workflow["details"] == wf_detail_put
    assert db_workflow["uses_mets_server"] == True

    assert workflow_dir1 == workflow_dir2, \
        f"Workflow dir paths should match, but does not: {workflow_dir1} != {workflow_dir2}"
    assert workflow_path1 != workflow_path2, \
        f"Workflow paths should not, but match: {workflow_path1} == {workflow_path2}"
    assert workflow_details1 != workflow_details2, \
        f"Workflow details should not, but match: {workflow_details1} == {workflow_details2}"


@mark.asyncio
async def _test_put_workflow_not_allowed(operandi, auth, bytes_template_workflow_with_ms):
    production_workflow_ids = [
        "template_workflow", "default_workflow", "odem_workflow",
        "template_workflow_with_MS", "default_workflow_with_MS", "odem_workflow_with_MS"
    ]

    # Try to replace a production workflow which should raise an error code of 405
    files = {"nextflow_script": bytes_template_workflow_with_ms}
    for workflow_id in production_workflow_ids:
        response = await operandi.put(url=f"/workflow/{workflow_id}", files=files, auth=auth)
        assert_response_status_code(response.status_code, expected_floor=4)


# Not implemented/planned in the WebAPI
@mark.asyncio
async def _test_delete_workflow():
    pass


# Not implemented/planned in the WebAPI
@mark.asyncio
async def _test_delete_workflow_non_existing():
    pass


@mark.asyncio
async def _test_get_workflow_script(operandi, auth, bytes_template_workflow):
    # Post a new workflow script
    response = await operandi.post(url="/workflow", files={"nextflow_script": bytes_template_workflow}, auth=auth)
    assert_response_status_code(response.status_code, expected_floor=2)
    workflow_id = response.json()['resource_id']
    assert_local_dir_workflow(workflow_id)
    # Get the same workflow script
    response = await operandi.get(url=f"/workflow/{workflow_id}", auth=auth)
    assert_response_status_code(response.status_code, expected_floor=2)
    print(response.headers)
    assert response.headers.get('content-disposition').find(".nf") > -1, \
        "filename should have the '.nf' extension"


@mark.asyncio
async def _test_get_workflow_non_existing(operandi, auth):
    non_workflow_id = "non_existing_workflow_id"
    response = await operandi.get(url=f"/workflow/{non_workflow_id}", auth=auth)
    assert_response_status_code(response.status_code, expected_floor=4)


# This is already implemented as a part of the harvester full cycle test
@mark.asyncio
async def _test_run_operandi_workflow():
    pass


# This is already implemented as a part of the harvester full cycle test
@mark.asyncio
async def _test_running_workflow_job_status():
    pass


@mark.asyncio
async def _test_convert_txt_to_nextflow_success(operandi, auth):
    dummy_file = BytesIO(WORKFLOW_DUMMY_TEXT.encode('utf-8'))
    files = {"txt_file": ("dummy.txt", dummy_file, "text/plain")}
    params = {"environment": "local", "with_mets_server": False}

    # Simulate uploading the text file for conversion via POST
    response = await operandi.post(url="/convert_workflow", files=files, auth=auth, params=params)
    nf_file_content = response.content.decode('utf-8')
    # Verify the status code and content
    assert_response_status_code(response.status_code, expected_floor=2)
    assert "params.mets_path" in nf_file_content
    assert "params.env_wrapper_cmd_core" not in nf_file_content
    assert "params.mets_socket_path" not in nf_file_content
    assert "merging_mets" in nf_file_content


@mark.asyncio
async def _test_convert_txt_to_nextflow_success_with_mets_server(operandi, auth):
    dummy_file = BytesIO(WORKFLOW_DUMMY_TEXT.encode('utf-8'))
    files = {"txt_file": ("dummy.txt", dummy_file, "text/plain")}
    params = {"environment": "local", "with_mets_server": True}

    # Simulate uploading the text file for conversion via POST
    response = await operandi.post(url="/convert_workflow", files=files, auth=auth, params=params)
    nf_file_content = response.content.decode('utf-8')
    # Verify the status code and content
    assert_response_status_code(response.status_code, expected_floor=2)
    assert "params.mets_path" in nf_file_content
    assert "params.env_wrapper_cmd_core" not in nf_file_content
    assert "params.mets_socket_path" in nf_file_content
    assert "merging_mets" not in nf_file_content


@mark.asyncio
async def _test_convert_txt_to_nextflow_auth_failure(operandi):
    dummy_text = "Some dummy text"
    dummy_file = BytesIO(dummy_text.encode('utf-8'))
    files = {"txt_file": ("dummy.txt", dummy_file, "text/plain")}
    params = {"environment": "local", "with_mets_server": False}
    auth = ('invalid_user', 'invalid_password')
    response = await operandi.post(url="/convert_workflow", files=files, auth=auth, params=params)

    # Verify the status code and error message for failed authentication
    assert_response_status_code(response.status_code, expected_floor=4)
    assert response.json()["detail"] == "Not found user account for email: invalid_user"


@mark.asyncio
async def _test_convert_txt_to_nextflow_validator_failure(operandi, auth):
    invalid_text = "Invalid ocrd process text"
    dummy_file = BytesIO(invalid_text.encode('utf-8'))
    files = {"txt_file": ("invalid.txt", dummy_file, "text/plain")}
    params = {"environment": "local", "with_mets_server": False}

    response = await operandi.post(url="/convert_workflow", files=files, auth=auth, params=params)
    assert_response_status_code(response.status_code, expected_floor=4)
    assert "Failed to validate the ocrd process workflow txt file" in response.json()["detail"]


@mark.asyncio
async def _test_convert_txt_to_nextflow_docker_success(operandi, auth):
    dummy_file = BytesIO(WORKFLOW_DUMMY_TEXT.encode('utf-8'))
    files = {"txt_file": ("dummy.txt", dummy_file, "text/plain")}
    params = {"environment": "docker", "with_mets_server": False}

    response = await operandi.post(url="/convert_workflow", files=files, auth=auth, params=params)
    nf_file_content = response.content.decode('utf-8')
    assert_response_status_code(response.status_code, expected_floor=2)
    assert "params.mets_path" in nf_file_content
    assert "params.env_wrapper_cmd_core" in nf_file_content
    assert "params.mets_socket_path" not in nf_file_content
    assert "merging_mets" in nf_file_content


@mark.asyncio
async def _test_convert_txt_to_nextflow_docker_success_with_mets_server(operandi, auth):
    dummy_file = BytesIO(WORKFLOW_DUMMY_TEXT.encode('utf-8'))
    files = {"txt_file": ("dummy.txt", dummy_file, "text/plain")}
    params = {"environment": "docker", "with_mets_server": True}

    response = await operandi.post(url="/convert_workflow", files=files, auth=auth, params=params)
    nf_file_content = response.content.decode('utf-8')
    assert_response_status_code(response.status_code, expected_floor=2)
    assert "params.mets_path" in nf_file_content
    assert "params.env_wrapper_cmd_core" in nf_file_content
    assert "params.mets_socket_path" in nf_file_content
    assert "merging_mets" not in nf_file_content
