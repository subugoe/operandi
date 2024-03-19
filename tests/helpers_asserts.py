from os.path import exists, isdir, isfile
from requests import get
from time import sleep


def assert_availability_db(url, tries: int = 6, wait_time: int = 10):
    http_url = url.replace("mongodb", "http")
    response = None
    while tries > 0:
        response = get(http_url)
        if response.status_code == 200:
            break
        sleep(wait_time)
        tries -= 1
    assert response.status_code == 200, f"DB not running on: {url}"


def assert_exists_ws_db_resource(ws_db, workspace_id: str):
    assert ws_db, "Workspace resource not existing in the database"
    assert ws_db.workspace_id, f"Non-existent workspace id: {workspace_id}"
    assert ws_db.workspace_id == workspace_id


def assert_exists_ws_db_resource_not(ws_db, workspace_id: str):
    # Note, the resource itself is not deleted, just the flag is set
    assert ws_db, "Workspace resource not existing in the database"
    assert ws_db.deleted, f"DB workspace resource entry should not exists, but does: {workspace_id}"


def assert_exists_wf_db_resource(wf_db, workflow_id: str):
    assert wf_db, "Workflow resource not existing in the database"
    assert wf_db.workflow_id, f"Non-existent workflow id: {workflow_id}"
    assert wf_db.workflow_id == workflow_id


def assert_exists_wf_db_resource_not(wf_db, workflow_id: str):
    # Note, the resource itself is not deleted, just the flag is set
    assert wf_db, "Resource not existing in the database"
    assert wf_db.deleted, f"DB workflow resource entry should not exists, but does: {workflow_id}"


def assert_exists_dir(dir_path: str):
    assert exists(dir_path), f"Path nonexistent: {dir_path}"
    assert isdir(dir_path), f"Path not directory: {dir_path}"


def assert_exists_file(file_path: str):
    assert exists(file_path), f"Path nonexistent: {file_path}"
    assert isfile(file_path), f"Path not file: {file_path}"


def assert_exists_not(check_path: str):
    assert not exists(check_path), f"Path should not but exists: {check_path}"
