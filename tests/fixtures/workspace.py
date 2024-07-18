from pytest import fixture
from tests.constants import WORKSPACES_ROUTER_DIR
from tests.helpers_utils import to_asset_path


@fixture(scope="package", name="path_dummy_workspace_data_dir")
def fixture_path_dummy_workspace_data_dir():
    yield to_asset_path(resource_type=WORKSPACES_ROUTER_DIR, name="dummy_ws/data")


@fixture(scope="package", name="path_small_workspace_data_dir")
def fixture_path_small_workspace_data_dir():
    yield to_asset_path(resource_type=WORKSPACES_ROUTER_DIR, name="small_ws/data")


@fixture(scope="package", name="path_dummy_workspace")
def fixture_path_dummy_workspace():
    yield to_asset_path(resource_type=WORKSPACES_ROUTER_DIR, name="dummy_ws.ocrd.zip")


@fixture(scope="package", name="path_ws_different_mets")
def fixture_path_ws_different_mets():
    yield to_asset_path(resource_type=WORKSPACES_ROUTER_DIR, name="example_ws_different_mets.ocrd.zip")


@fixture(scope="package", name="path_small_workspace")
def fixture_path_small_workspace():
    yield to_asset_path(resource_type=WORKSPACES_ROUTER_DIR, name="small_ws.ocrd.zip")


@fixture(scope="package", name="bytes_dummy_workspace")
def fixture_bytes_dummy_workspace(path_dummy_workspace):
    return open(file=path_dummy_workspace, mode="rb")


@fixture(scope="package", name="bytes_ws_different_mets")
def fixture_bytes_ws_different_mets(path_ws_different_mets):
    return open(file=path_ws_different_mets, mode="rb")


@fixture(scope="package", name="bytes_small_workspace")
def fixture_bytes_small_workspace(path_small_workspace):
    return open(file=path_small_workspace, mode="rb")
