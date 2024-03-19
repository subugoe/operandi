from os import environ
from os.path import join
from operandi_server.constants import SERVER_WORKSPACES_ROUTER
from operandi_utils.database import sync_db_get_workspace, sync_db_update_workspace
from operandi_utils import StateWorkspace

from tests.helpers_asserts import assert_exists_ws_db_resource, assert_exists_ws_db_resource_not
from .helpers_asserts import assert_local_dir_workspace, assert_local_dir_workspace_not

"""
def test_post_workspace_url(operandi, auth):
    mets_url = "https://content.staatsbibliothek-berlin.de/dc/PPN631277528.mets.xml"
    # Separate with `,` to add a second file group to be preserved, e.g., `DEFAULT,MAX`
    preserve_file_grps = "DEFAULT"
    request_url = f"/import_external_workspace?mets_url={mets_url}&preserve_file_grps={preserve_file_grps}"
    response = operandi.post(url=request_url, auth=auth)
    assert response.status_code == 201
    ws_id = response.json()["resource_id"]
    ws_db = sync_db_get_workspace(workspace_id=ws_id)
    assert_exists_ws_db_resource(ws_db, workspace_id=ws_id)
    assert_local_dir_workspace(ws_id)


def test_post_workspace_zip(operandi, auth, bytes_dummy_workspace):
    ws_file = {"workspace": bytes_dummy_workspace}
    response = operandi.post(url="/workspace", files=ws_file, auth=auth)
    assert response.status_code == 201
    ws_id = response.json()["resource_id"]
    ws_db = sync_db_get_workspace(workspace_id=ws_id)
    assert_exists_ws_db_resource(ws_db, workspace_id=ws_id)
    assert_local_dir_workspace(ws_id)


def test_post_workspace_zip_different_mets(operandi, auth, bytes_ws_different_mets):
    ws_file = {"workspace": bytes_ws_different_mets}
    response = operandi.post(url="/workspace", files=ws_file, auth=auth)
    assert response.status_code == 201
    ws_id = response.json()["resource_id"]
    ws_db = sync_db_get_workspace(workspace_id=ws_id)
    assert_exists_ws_db_resource(ws_db, workspace_id=ws_id)
    assert_local_dir_workspace(ws_id)


def test_put_workspace_zip(operandi, auth, bytes_dummy_workspace, bytes_ws_different_mets):
    put_ws_id = "put_workspace_id"
    # The first put request creates a new workspace
    ws_file = {"workspace": bytes_dummy_workspace}
    response = operandi.put(url=f"/workspace/{put_ws_id}", files=ws_file, auth=auth)
    assert response.status_code == 201
    ws_id = response.json()["resource_id"]
    ws_db = sync_db_get_workspace(workspace_id=ws_id)
    assert_exists_ws_db_resource(ws_db, workspace_id=ws_id)
    assert_local_dir_workspace(ws_id)

    ocrd_identifier1 = ws_db.ocrd_identifier
    assert ocrd_identifier1, "Failed to extract ocrd identifier 1"

    # The second put request replaces the previously created workspace
    ws_file_diff = {"workspace": bytes_ws_different_mets}
    response = operandi.put(f"/workspace/{put_ws_id}", files=ws_file_diff, auth=auth)
    assert response.status_code == 201
    ws_id = response.json()["resource_id"]

    db_workspace = sync_db_get_workspace(workspace_id=ws_id)
    assert_exists_ws_db_resource(ws_db, workspace_id=ws_id)
    assert_local_dir_workspace(ws_id)

    ocrd_identifier2 = db_workspace.ocrd_identifier
    assert ocrd_identifier2, "Failed to extract ocrd identifier 2"
    assert ocrd_identifier1 != ocrd_identifier2, \
        f"Ocrd identifiers should not, but match: {ocrd_identifier1} == {ocrd_identifier2}"


def test_delete_workspace(operandi, auth, bytes_ws_different_mets):
    # Post a workspace
    ws_file = {"workspace": bytes_ws_different_mets}
    response = operandi.post(url="/workspace", files=ws_file, auth=auth)
    assert response.status_code == 201
    posted_ws_id = response.json()["resource_id"]

    ws_db = sync_db_get_workspace(workspace_id=posted_ws_id)
    assert_exists_ws_db_resource(ws_db, workspace_id=posted_ws_id)
    assert_local_dir_workspace(posted_ws_id)

    # Delete the previously posted workspace
    delete_ws_id = posted_ws_id
    response = operandi.delete(f"/workspace/{delete_ws_id}", auth=auth)
    assert response.status_code == 200
    ws_db_deleted = sync_db_get_workspace(workspace_id=posted_ws_id)
    assert_exists_ws_db_resource_not(ws_db_deleted, workspace_id=delete_ws_id)
    assert_local_dir_workspace_not(delete_ws_id)


def test_delete_workspace_non_existing(operandi, auth, bytes_ws_different_mets):
    ws_file = {"workspace": bytes_ws_different_mets}
    response = operandi.post("/workspace", files=ws_file, auth=auth)
    posted_ws_id = response.json()["resource_id"]
    delete_ws_id = posted_ws_id
    response = operandi.delete(f"/workspace/{delete_ws_id}", auth=auth)
    assert response.status_code == 200  # delete success
    response = operandi.delete(f"/workspace/{delete_ws_id}", auth=auth)
    assert response.status_code == 410  # already deleted


def test_get_workspace(operandi, auth, bytes_ws_different_mets):
    ws_file = {"workspace": bytes_ws_different_mets}
    response = operandi.post("/workspace", files=ws_file, auth=auth)
    ws_id = response.json()["resource_id"]
    response = operandi.get(f"/workspace/{ws_id}", auth=auth)
    assert response.status_code == 200
    print(response.headers)
    assert response.headers.get("content-type").find("zip") > -1, "content-type should be something with 'zip'"

    # TODO: Use a method that resolves with ID
    zip_local_path = join(
        environ.get("OPERANDI_SERVER_BASE_DIR"),
        SERVER_WORKSPACES_ROUTER,
        f"{ws_id}.zip"
    )
    with open(zip_local_path, "wb") as filePtr:
        for chunk in response.iter_bytes(chunk_size=1024):
            if chunk:
                filePtr.write(chunk)


def test_get_workspace_non_existing(operandi, auth):
    non_ws_id = "non_existing_workspace_id"
    response = operandi.get(f"/workspace/{non_ws_id}", auth=auth)
    assert response.status_code == 404


def test_get_not_ready_workspace(operandi, auth, bytes_dummy_workspace):
    ws_file = {"workspace": bytes_dummy_workspace}
    response = operandi.post("/workspace", files=ws_file, auth=auth)
    assert response.status_code == 201
    ws_id = response.json()["resource_id"]

    ws_db = sync_db_get_workspace(workspace_id=ws_id)
    assert_exists_ws_db_resource(ws_db, workspace_id=ws_id)
    assert_local_dir_workspace(ws_id)

    sync_db_update_workspace(find_workspace_id=ws_id, state=StateWorkspace.TRANSFERRING_TO_HPC)
    response = operandi.get(f"/workspace/{ws_id}", auth=auth)
    assert response.status_code == 403  # State not READY
"""