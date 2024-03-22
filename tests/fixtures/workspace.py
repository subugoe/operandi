from pytest import fixture
from tests.helpers_utils import to_asset_path

WORKSPACES_ROUTER_DIR = "workspaces"


@fixture(scope="package", name="path_dummy_workspace_data_dir")
def fixture_path_dummy_workspace_data_dir():
    yield to_asset_path(WORKSPACES_ROUTER_DIR, "dummy_ws/data")


@fixture(scope="package", name="path_small_workspace_data_dir")
def fixture_path_small_workspace_data_dir():
    yield to_asset_path(WORKSPACES_ROUTER_DIR, "small_ws/data")


@fixture(scope="package", name="path_dummy_workspace")
def fixture_path_dummy_workspace():
    yield to_asset_path(WORKSPACES_ROUTER_DIR, "dummy_ws.ocrd.zip")


@fixture(scope="package", name="path_ws_different_mets")
def fixture_path_ws_different_mets():
    yield to_asset_path(WORKSPACES_ROUTER_DIR, "example_ws_different_mets.ocrd.zip")


@fixture(scope="package", name="path_small_workspace")
def fixture_path_small_workspace():
    yield to_asset_path(WORKSPACES_ROUTER_DIR, "small_ws.ocrd.zip")


@fixture(scope="package", name="bytes_dummy_workspace")
def fixture_bytes_dummy_workspace(path_dummy_workspace):
    return open(path_dummy_workspace, "rb")


@fixture(scope="package", name="bytes_ws_different_mets")
def fixture_bytes_ws_different_mets(path_ws_different_mets):
    return open(path_ws_different_mets, "rb")


@fixture(scope="package", name="bytes_small_workspace")
def fixture_bytes_small_workspace(path_small_workspace):
    return open(path_small_workspace, "rb")
