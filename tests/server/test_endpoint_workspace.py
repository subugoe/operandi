from ..helpers_asserts import assert_exists_db_resource
from .helpers_asserts import (
    assert_local_dir_workspace,
    assert_response_status_code
)


# Disabled test - takes 13 secs to finish...
def _test_post_workspace_url(operandi, workspace_collection, auth):
    mets_url = "https://content.staatsbibliothek-berlin.de/dc/PPN631277528.mets.xml"
    response = operandi.post(
        url=f"/workspace/import_external?mets_url={mets_url}",
        auth=auth
    )
    assert_response_status_code(response.status_code, expected_floor=2)
    workspace_id = response.json()['resource_id']
    assert_local_dir_workspace(workspace_id)

    # Database checks
    db_workspace = workspace_collection.find_one({"workspace_id": workspace_id})
    assert_exists_db_resource(db_workspace, "workspace_id", workspace_id)


def test_post_workspace_zip(operandi, workspace_collection, workspace1, auth):
    response = operandi.post("/workspace", files=workspace1, auth=auth)
    assert_response_status_code(response.status_code, expected_floor=2)
    workspace_id = response.json()['resource_id']
    assert_local_dir_workspace(workspace_id)
    db_workspace = workspace_collection.find_one({"workspace_id": workspace_id})
    assert_exists_db_resource(db_workspace, "workspace_id", workspace_id)


def test_post_workspace_zip_different_mets(operandi, auth, workspace_collection, workspace2):
    response = operandi.post("/workspace", files=workspace2, auth=auth)
    assert_response_status_code(response.status_code, expected_floor=2)
    workspace_id = response.json()['resource_id']
    assert_local_dir_workspace(workspace_id)
    db_workspace = workspace_collection.find_one({"workspace_id": workspace_id})
    assert_exists_db_resource(db_workspace, "workspace_id", workspace_id)


# Test is broken
def test_put_workspace_zip(operandi, auth, workspace_collection, workspace1, workspace2):
    put_workspace_id = "put_workspace_id"
    # The first put request creates a new workspace
    response = operandi.put(f"/workspace/{put_workspace_id}", files=workspace1, auth=auth)
    assert_response_status_code(response.status_code, expected_floor=2)
    workspace_id = response.json()['resource_id']
    assert_local_dir_workspace(workspace_id)
    db_workspace = workspace_collection.find_one({"workspace_id": workspace_id})
    assert_exists_db_resource(db_workspace, "workspace_id", workspace_id)

    ocrd_identifier1 = db_workspace["ocrd_identifier"]
    assert ocrd_identifier1, "Failed to extract ocrd identifier 1"

    # The second put request replaces the previously created workspace
    response = operandi.put(f"/workspace/{put_workspace_id}", files=workspace2, auth=auth)
    assert_response_status_code(response.status_code, expected_floor=2)
    workspace_id = response.json()['resource_id']
    assert_local_dir_workspace(workspace_id)
    db_workspace = workspace_collection.find_one({"workspace_id": workspace_id})
    assert_exists_db_resource(db_workspace, "workspace_id", workspace_id)

    ocrd_identifier2 = db_workspace["ocrd_identifier"]
    assert ocrd_identifier2, "Failed to extract ocrd identifier 2"

    assert ocrd_identifier1 != ocrd_identifier2, \
        f"Ocrd identifiers mismatch: {ocrd_identifier1} != {ocrd_identifier2}"
