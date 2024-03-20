from pytest import fixture
from tests.helpers.utils import to_asset_path


@fixture(scope="package", name="path_dummy_workspace")
def fixture_path_dummy_workspace():
    yield to_asset_path("workspaces", "dummy_ws.ocrd.zip")


@fixture(scope="package", name="path_ws_different_mets")
def fixture_path_ws_different_mets():
    yield to_asset_path("workspaces", "example_ws_different_mets.ocrd.zip")


@fixture(scope="package", name="path_small_workspace")
def fixture_path_small_workspace():
    yield to_asset_path("workspaces", "small_ws.ocrd.zip")


@fixture(scope="package", name="bytes_dummy_workspace")
def fixture_bytes_dummy_workspace(path_dummy_workspace):
    return open(path_dummy_workspace, "rb")


@fixture(scope="package", name="bytes_ws_different_mets")
def fixture_bytes_ws_different_mets(path_ws_different_mets):
    return open(path_ws_different_mets, "rb")


@fixture(scope="package", name="bytes_small_workspace")
def fixture_bytes_small_workspace(path_small_workspace):
    return open(path_small_workspace, "rb")
