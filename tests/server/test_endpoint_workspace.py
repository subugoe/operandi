from ..conftest import OPERANDI_TESTS_DIR


def parse_resource_id(response):
    try:
        return response.json()['resource_id']
    except (AttributeError, KeyError):
        return None


def assert_status_code(status_code, expected_floor):
    status_floor = status_code // 100
    assert expected_floor == status_floor, \
        f"Response status code expected:{expected_floor}xx, got: {status_code}."


def assert_db_entry_created(resource_from_db, resource_id, db_key):
    assert resource_from_db, \
        "Resource entry was not created in mongodb"
    db_id = resource_from_db[db_key]
    assert db_id == resource_id, \
        f"Wrong resource id. Expected: {resource_id}, found {db_id}"


def assert_workspace_dir(workspace_id):
    workspace_dir = f"{OPERANDI_TESTS_DIR}/workspaces/{workspace_id}"
    assert workspace_dir, "workspace-dir not existing"


def test_post_workspace(operandi_client, auth, workspace_mongo_coll, asset_workspace1):
    """
    mets_url = "https%3A%2F%2Fcontent.staatsbibliothek-berlin.de%2Fdc%2FPPN631277528.mets.xml"
    response = operandi_client.post(
        url=f"/workspace/import_external?mets_url={mets_url}",
        auth=auth
    )
    """

    response = operandi_client.post("/workspace", files=asset_workspace1, auth=auth)
    print(response.json())
    assert_status_code(response.status_code, expected_floor=2)
    workspace_id = parse_resource_id(response)
    assert_workspace_dir(workspace_id)

    # Database checks
    resource_from_db = workspace_mongo_coll.find_one({"workspace_id": workspace_id})
    assert_db_entry_created(resource_from_db, workspace_id, db_key="workspace_id")
