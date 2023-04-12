from os.path import exists, join


def parse_resource_id(response):
    try:
        return response.json()['resource_id']
    except (AttributeError, KeyError):
        return None


def assert_status_code(status_code, expected_floor):
    status_floor = status_code // 100
    assert expected_floor == status_floor, \
        f"Response status code expected:{expected_floor}xx, got: {status_code}."


def assert_db_entry_created(resource_from_db, resource_id, db_key="_id"):
    assert resource_from_db, \
        "Resource entry was not created in mongodb"
    db_id = resource_from_db[db_key]
    assert db_id == resource_id, \
        "Wrong resource id. Expected: {resource_id}, found {db_id}"


def assert_workspace_dir(workspace_id):
    assert exists(join("/tmp/ocrd-webapi-data/workspaces", workspace_id)), \
        "workspace-dir not existing"


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
    resource_from_db = workspace_mongo_coll.find_one()
    assert_db_entry_created(resource_from_db, workspace_id)
