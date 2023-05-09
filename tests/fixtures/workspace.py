from pytest import fixture
from tests.helpers_utils import to_asset_path


@fixture(scope="session", name="path_workspace1")
def fixture_path_workspace1():
    yield to_asset_path("workspaces", "dummy_ws.ocrd.zip")


@fixture(scope="session", name="path_workspace2")
def fixture_path_workspace2():
    yield to_asset_path("workspaces", "example_ws_different_mets.ocrd.zip")


@fixture(scope="session", name="bytes_workspace1")
def fixture_bytes_workspace1(path_workspace1):
    return open(path_workspace1, 'rb')


@fixture(scope="session", name="bytes_workspace2")
def fixture_bytes_workspace2(path_workspace2):
    return open(path_workspace2, 'rb')
