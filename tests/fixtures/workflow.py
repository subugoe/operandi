from pytest import fixture
from tests.helpers_utils import to_asset_path


@fixture(scope="session", name="path_workflow1")
def fixture_path_workflow1():
    yield to_asset_path("workflows", "test_template_workflow.nf")


@fixture(scope="session", name="path_workflow2")
def fixture_path_workflow2():
    yield to_asset_path("workflows", "test_default_workflow.nf")


@fixture(scope="session", name="bytes_workflow1")
def fixture_bytes_workflow1(path_workflow1):
    return open(path_workflow1, 'rb')


@fixture(scope="session", name="bytes_workflow2")
def fixture_bytes_workflow2(path_workflow2):
    return open(path_workflow2, 'rb')
