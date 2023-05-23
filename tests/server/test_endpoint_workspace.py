from tests.helpers_asserts import (
    assert_exists_db_resource,
    assert_exists_db_resource_not
)
from .helpers_asserts import (
    assert_local_dir_workspace,
    assert_local_dir_workspace_not,
    assert_response_status_code
)


# Disabled test - takes 13 secs to finish...
def _test_post_workspace_url(operandi, auth, workspace_collection):
    mets_url = "https://content.staatsbibliothek-berlin.de/dc/PPN631277528.mets.xml"
    response = operandi.post(
        url=f"/workspace/import_external?mets_url={mets_url}",
        auth=auth
    )
    assert_response_status_code(response.status_code, expected_floor=2)
    workspace_id = response.json()['resource_id']
    assert_local_dir_workspace(workspace_id)
    db_workspace = workspace_collection.find_one(
        {"workspace_id": workspace_id}
    )
    assert_exists_db_resource(db_workspace, "workspace_id", workspace_id)


def test_post_workspace_zip(operandi, auth, workspace_collection, bytes_workspace1):
    response = operandi.post(
        "/workspace",
        files={"workspace": bytes_workspace1},
        auth=auth
    )
    assert_response_status_code(response.status_code, expected_floor=2)
    workspace_id = response.json()['resource_id']
    assert_local_dir_workspace(workspace_id)
    db_workspace = workspace_collection.find_one(
        {"workspace_id": workspace_id}
    )
    assert_exists_db_resource(db_workspace, "workspace_id", workspace_id)


def test_post_workspace_zip_different_mets(operandi, auth, workspace_collection, bytes_workspace2):
    response = operandi.post(
        "/workspace",
        files={"workspace": bytes_workspace2},
        auth=auth
    )
    assert_response_status_code(response.status_code, expected_floor=2)
    workspace_id = response.json()['resource_id']
    assert_local_dir_workspace(workspace_id)
    db_workspace = workspace_collection.find_one(
        {"workspace_id": workspace_id}
    )
    assert_exists_db_resource(db_workspace, "workspace_id", workspace_id)


def test_put_workspace_zip(operandi, auth, workspace_collection, bytes_workspace1, bytes_workspace2):
    put_workspace_id = "put_workspace_id"
    # The first put request creates a new workspace
    response = operandi.put(
        f"/workspace/{put_workspace_id}",
        files={"workspace": bytes_workspace1},
        auth=auth
    )
    assert_response_status_code(response.status_code, expected_floor=2)
    workspace_id = response.json()['resource_id']
    assert_local_dir_workspace(workspace_id)
    db_workspace = workspace_collection.find_one(
        {"workspace_id": workspace_id}
    )
    assert_exists_db_resource(db_workspace, "workspace_id", workspace_id)

    ocrd_identifier1 = db_workspace["ocrd_identifier"]
    assert ocrd_identifier1, "Failed to extract ocrd identifier 1"

    # The second put request replaces the previously created workspace
    response = operandi.put(
        f"/workspace/{put_workspace_id}",
        files={"workspace": bytes_workspace2},
        auth=auth
    )
    assert_response_status_code(response.status_code, expected_floor=2)
    workspace_id = response.json()['resource_id']
    assert_local_dir_workspace(workspace_id)
    db_workspace = workspace_collection.find_one(
        {"workspace_id": workspace_id}
    )
    assert_exists_db_resource(db_workspace, "workspace_id", workspace_id)

    ocrd_identifier2 = db_workspace["ocrd_identifier"]
    assert ocrd_identifier2, "Failed to extract ocrd identifier 2"

    assert ocrd_identifier1 != ocrd_identifier2, \
        f"Ocrd identifiers should not, but match: {ocrd_identifier1} == {ocrd_identifier2}"


def test_delete_workspace(operandi, auth, workspace_collection, bytes_workspace2):
    # Post a workspace
    response = operandi.post(
        "/workspace",
        files={"workspace": bytes_workspace2},
        auth=auth
    )
    posted_workspace_id = response.json()['resource_id']
    assert_response_status_code(response.status_code, expected_floor=2)
    assert_local_dir_workspace(posted_workspace_id)
    db_workspace = workspace_collection.find_one(
        {"workspace_id": posted_workspace_id}
    )
    assert_exists_db_resource(db_workspace, "workspace_id", posted_workspace_id)

    # Delete the previously posted workspace
    delete_workspace_id = posted_workspace_id
    response = operandi.delete(
        f"/workspace/{delete_workspace_id}",
        auth=auth
    )
    assert_response_status_code(response.status_code, expected_floor=2)
    assert_local_dir_workspace_not(delete_workspace_id)
    db_deleted_workspace = workspace_collection.find_one(
        {"workspace_id": delete_workspace_id}
    )
    assert_exists_db_resource_not(db_deleted_workspace, delete_workspace_id)


# TODO for the WebAPI: Non-existing resource should not return an exception to the user!
def _test_delete_workspace_non_existing(operandi, auth, bytes_workspace2):
    response = operandi.post(
        "/workspace",
        files={"workspace": bytes_workspace2},
        auth=auth
    )
    posted_workspace_id = response.json()['resource_id']
    delete_workspace_id = posted_workspace_id
    response = operandi.delete(f"/workspace/{delete_workspace_id}", auth=auth)
    assert_response_status_code(response.status_code, expected_floor=2)  # Deleted
    response = operandi.delete(f"/workspace/{delete_workspace_id}", auth=auth)
    assert_response_status_code(response.status_code, expected_floor=4)  # Not available


def test_get_workspace(operandi, auth, bytes_workspace2):
    response = operandi.post(
        "/workspace",
        files={"workspace": bytes_workspace2},
        auth=auth
    )
    workspace_id = response.json()['resource_id']
    response = operandi.get(
        f"/workspace/{workspace_id}",
        headers={"accept": "application/vnd.ocrd+zip"},
        auth=auth
    )
    assert_response_status_code(response.status_code, expected_floor=2)
    print(response.headers)
    assert response.headers.get('content-type').find("zip") > -1, \
        "content-type should be something with 'zip'"


# TODO for the WebAPI: Non-existing resource should not return an exception to the user!
def _test_get_workspace_non_existing(operandi, auth):
    non_workspace_id = "non_existing_workspace_id"
    response = operandi.get(
        f"/workspace/{non_workspace_id}",
        headers={"accept": "application/vnd.ocrd+zip"},
        auth=auth
    )
    assert_response_status_code(response.status_code, expected_floor=4)
