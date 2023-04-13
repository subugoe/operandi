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


def test_post_workspace_zip(operandi, workspace_collection, fixture_workspace1, auth):
    response = operandi.post("/workspace", files=fixture_workspace1, auth=auth)
    assert_response_status_code(response.status_code, expected_floor=2)
    workspace_id = response.json()['resource_id']
    assert_local_dir_workspace(workspace_id)

    # Database checks
    db_workspace = workspace_collection.find_one({"workspace_id": workspace_id})
    assert_exists_db_resource(db_workspace, "workspace_id", workspace_id)
