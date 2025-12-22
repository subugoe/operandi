from os import environ
from os.path import join

from ocrd import Resolver
from ocrd.workspace import Workspace

from operandi_server.constants import SERVER_WORKSPACES_ROUTER

from tests.helpers_asserts import assert_exists_db_resource, assert_exists_db_resource_not
from .helpers_asserts import assert_local_dir_workspace, assert_local_dir_workspace_not, assert_response_status_code


def _test_post_workspace_url(operandi, auth, db_workspaces):
    ws_detail = "Test url workspace - https://content.staatsbibliothek-berlin.de/dc/PPN631277528.mets.xml"
    mets_url = "https://content.staatsbibliothek-berlin.de/dc/PPN631277528.mets.xml"
    # Separate with `,` to add a second file group to be preserved, e.g., `DEFAULT,MAX`
    preserve_file_grps = "DEFAULT"
    req_url = (
        f"/import_external_workspace"
        f"?mets_url={mets_url}"
        f"&preserve_file_grps={preserve_file_grps}"
        f"&details={ws_detail}"
    )
    response = operandi.post(url=req_url, auth=auth)
    assert_response_status_code(response.status_code, expected_floor=2)
    workspace_id = response.json()['resource_id']
    assert_local_dir_workspace(workspace_id)
    db_workspace = db_workspaces.find_one({"workspace_id": workspace_id})
    assert_exists_db_resource(db_workspace, resource_key="workspace_id", resource_id=workspace_id)
    assert db_workspace["details"] == ws_detail


def test_post_workspace_zip(operandi, auth, db_workspaces, bytes_dummy_workspace):
    ws_detail = "Test dummy workspace"
    response = operandi.post(
        url=f"/workspace?details={ws_detail}", files={"workspace": bytes_dummy_workspace}, auth=auth)
    assert_response_status_code(response.status_code, expected_floor=2)
    workspace_id = response.json()['resource_id']
    assert_local_dir_workspace(workspace_id)
    db_workspace = db_workspaces.find_one({"workspace_id": workspace_id})
    assert_exists_db_resource(db_workspace, resource_key="workspace_id", resource_id=workspace_id)
    assert db_workspace["details"] == ws_detail


def test_post_workspace_zip_different_mets(operandi, auth, db_workspaces, bytes_ws_different_mets):
    ws_detail = "Test different mets basename workspace"
    response = operandi.post(
        url=f"/workspace?details={ws_detail}", files={"workspace": bytes_ws_different_mets}, auth=auth)
    assert_response_status_code(response.status_code, expected_floor=2)
    workspace_id = response.json()['resource_id']
    assert_local_dir_workspace(workspace_id)
    db_workspace = db_workspaces.find_one({"workspace_id": workspace_id})
    assert_exists_db_resource(db_workspace, resource_key="workspace_id", resource_id=workspace_id)
    assert db_workspace["details"] == ws_detail


def test_put_workspace_zip(operandi, auth, db_workspaces, bytes_dummy_workspace, bytes_ws_different_mets):
    put_workspace_id = "put_workspace_id"
    ws_detail = "Test workspace"
    ws_detail_put = "Test put workspace"
    req_url = f"/workspace/{put_workspace_id}"

    # The first put request creates a new workspace
    response = operandi.put(
        url=f"{req_url}?details={ws_detail}", files={"workspace": bytes_dummy_workspace}, auth=auth)
    assert_response_status_code(response.status_code, expected_floor=2)
    workspace_id = response.json()['resource_id']
    assert_local_dir_workspace(workspace_id)
    db_workspace = db_workspaces.find_one({"workspace_id": workspace_id})
    assert_exists_db_resource(db_workspace, resource_key="workspace_id", resource_id=workspace_id)
    assert db_workspace["details"] == ws_detail

    ocrd_identifier1 = db_workspace["ocrd_identifier"]
    assert ocrd_identifier1, "Failed to extract ocrd identifier 1"
    ws_detail1 = db_workspace["details"]

    # The second put request replaces the previously created workspace
    response = operandi.put(
        url=f"{req_url}?details={ws_detail_put}", files={"workspace": bytes_ws_different_mets}, auth=auth)
    assert_response_status_code(response.status_code, expected_floor=2)
    workspace_id = response.json()['resource_id']
    assert_local_dir_workspace(workspace_id)
    db_workspace = db_workspaces.find_one({"workspace_id": workspace_id})
    assert_exists_db_resource(db_workspace, resource_key="workspace_id", resource_id=workspace_id)
    assert db_workspace["details"] == ws_detail_put

    ocrd_identifier2 = db_workspace["ocrd_identifier"]
    assert ocrd_identifier2, "Failed to extract ocrd identifier 2"
    ws_detail2 = db_workspace["details"]
    assert ocrd_identifier1 != ocrd_identifier2, \
        f"Ocrd identifiers should not, but match: {ocrd_identifier1} == {ocrd_identifier2}"
    assert ws_detail1 != ws_detail2, \
        f"Workspace details should not, but match: {ws_detail1} == {ws_detail2}"

def test_delete_workspace(operandi, auth, db_workspaces, bytes_ws_different_mets):
    # Post a workspace
    response = operandi.post(url="/workspace", files={"workspace": bytes_ws_different_mets}, auth=auth)
    posted_workspace_id = response.json()['resource_id']
    assert_response_status_code(response.status_code, expected_floor=2)
    assert_local_dir_workspace(posted_workspace_id)
    db_workspace = db_workspaces.find_one({"workspace_id": posted_workspace_id})
    assert_exists_db_resource(db_workspace, resource_key="workspace_id", resource_id=posted_workspace_id)

    # Delete the previously posted workspace
    delete_workspace_id = posted_workspace_id
    response = operandi.delete(url=f"/workspace/{delete_workspace_id}", auth=auth)
    assert_response_status_code(response.status_code, expected_floor=2)
    assert_local_dir_workspace_not(delete_workspace_id)
    db_deleted_workspace = db_workspaces.find_one({"workspace_id": delete_workspace_id})
    assert_exists_db_resource_not(db_deleted_workspace, delete_workspace_id)


def test_delete_workspace_non_existing(operandi, auth, bytes_ws_different_mets):
    response = operandi.post(url="/workspace", files={"workspace": bytes_ws_different_mets}, auth=auth)
    posted_workspace_id = response.json()['resource_id']
    delete_workspace_id = posted_workspace_id
    response = operandi.delete(f"/workspace/{delete_workspace_id}", auth=auth)
    assert_response_status_code(response.status_code, expected_floor=2)  # Deleted
    response = operandi.delete(f"/workspace/{delete_workspace_id}", auth=auth)
    assert_response_status_code(response.status_code, expected_floor=4)  # Not available


def test_get_workspace(operandi, auth, bytes_ws_different_mets):
    response = operandi.post(url="/workspace", files={"workspace": bytes_ws_different_mets}, auth=auth)
    workspace_id = response.json()['resource_id']
    response = operandi.get(url=f"/workspace/{workspace_id}", auth=auth)
    assert_response_status_code(response.status_code, expected_floor=2)
    print(response.headers)
    assert response.headers.get('content-type').find("zip") > -1, \
        "content-type should be something with 'zip'"

    # TODO: Use a method that resolves with ID
    zip_local_path = join(environ.get("OPERANDI_SERVER_BASE_DIR"), SERVER_WORKSPACES_ROUTER, f"{workspace_id}.zip")
    with open(zip_local_path, 'wb') as filePtr:
        for chunk in response.iter_bytes(chunk_size=1024):
            if chunk:
                filePtr.write(chunk)


def test_get_workspace_non_existing(operandi, auth):
    non_workspace_id = "non_existing_workspace_id"
    response = operandi.get(url=f"/workspace/{non_workspace_id}", auth=auth)
    assert_response_status_code(response.status_code, expected_floor=4)


def test_delete_file_groups(operandi, auth, db_workspaces, bytes_dummy_workspace):
    response = operandi.post(url="/workspace", files={"workspace": bytes_dummy_workspace}, auth=auth)
    assert_response_status_code(response.status_code, expected_floor=2)
    workspace_id = response.json()['resource_id']
    assert_local_dir_workspace(workspace_id)
    db_workspace = db_workspaces.find_one({"workspace_id": workspace_id})
    assert_exists_db_resource(db_workspace, resource_key="workspace_id", resource_id=workspace_id)

    workspace: Workspace = Resolver().workspace_from_url(
        mets_url=db_workspace["workspace_mets_path"], mets_basename=db_workspace["mets_basename"], download=False
    )
    file_groups_amount_old = len(workspace.mets.file_groups)

    # Remove non-existing file groups - silently ignored
    remove_file_grps = "DEFAULT"
    req_url = f"/remove_file_group/{workspace_id}?remove_file_grps={remove_file_grps}"
    response = operandi.delete(url=req_url, auth=auth)
    assert_response_status_code(response.status_code, expected_floor=2)
    workspace.reload_mets()
    assert len(workspace.mets.file_groups) == file_groups_amount_old

    # Remove existing file group
    remove_file_grps = "OCR-D-IMG"
    req_url = f"/remove_file_group/{workspace_id}?remove_file_grps={remove_file_grps}"
    response = operandi.delete(url=req_url, auth=auth)
    assert_response_status_code(response.status_code, expected_floor=2)
    workspace.reload_mets()
    assert len(workspace.mets.file_groups) == file_groups_amount_old - 1
