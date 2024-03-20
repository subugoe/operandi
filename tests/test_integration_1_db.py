from os.path import join
from pytest import raises
from src.utils.operandi_utils.database import (
    sync_db_create_workspace,
    sync_db_get_workspace,
    sync_db_update_workspace
)
from tests.helpers.utils import to_asset_path


def test_db_workspace_create():
    ws_id = "test_ws_id"
    ws_dir = to_asset_path(resource_type="workspaces/dummy_ws", name="data")
    mets_path = join(ws_dir, "mets.xml")
    bag_info = {
        "Bag-Software-Agent": "ocrd/core 2.45.1 (bagit.py 1.8.1, bagit_profile 1.3.1)",
        "BagIt-Profile-Identifier": "https://ocr-d.github.io/bagit-profile.json",
        "Bagging-Date": "2023-04-12 13:24:54.626258",
        "Ocrd-Identifier": "dummy_ws",
        "Payload-Oxum": "699185.2"
    }
    db_created_workspace = sync_db_create_workspace(
        workspace_id=ws_id, workspace_dir=ws_dir, pages_amount=1, bag_info=bag_info
    )
    assert db_created_workspace
    assert db_created_workspace.workspace_mets_path == mets_path
    db_found_workspace = sync_db_get_workspace(workspace_id=ws_id)
    assert db_found_workspace
    assert db_found_workspace == db_created_workspace

    with raises(RuntimeError):
        sync_db_get_workspace(workspace_id="non-existing-id")


def test_db_workspace_update():
    ws_id = "test_ws_id2"
    ws_dir = to_asset_path(resource_type="workspaces/dummy_ws", name="data")
    mets_path = join(ws_dir, "mets.xml")
    bag_info = {
        "Bag-Software-Agent": "ocrd/core 2.45.1 (bagit.py 1.8.1, bagit_profile 1.3.1)",
        "BagIt-Profile-Identifier": "https://ocr-d.github.io/bagit-profile.json",
        "Bagging-Date": "2023-04-12 13:24:54.626258",
        "Ocrd-Identifier": "dummy_ws",
        "Payload-Oxum": "699185.2"
    }
    db_created_workspace = sync_db_create_workspace(
        workspace_id=ws_id, workspace_dir=ws_dir, pages_amount=1, bag_info=bag_info
    )
    assert db_created_workspace
    db_found_workspace = sync_db_get_workspace(workspace_id=ws_id)
    assert db_found_workspace
    assert db_created_workspace == db_found_workspace

    update_to_pages = 4
    db_updated_workspace = sync_db_update_workspace(find_workspace_id=ws_id, pages_amount=update_to_pages)
    assert db_updated_workspace
    assert db_updated_workspace != db_created_workspace

    db_found_updated_workspace = sync_db_get_workspace(workspace_id=ws_id)
    assert db_found_updated_workspace
    assert db_found_updated_workspace.workspace_mets_path == mets_path
    assert db_found_updated_workspace.pages_amount == update_to_pages
    assert db_found_updated_workspace == db_updated_workspace
