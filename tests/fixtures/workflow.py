from pytest import fixture
from tests.helpers_utils import to_asset_path


@fixture(scope="package", name="template_workflow")
def fixture_template_workflow():
    yield to_asset_path("workflows", "test_template_workflow.nf")


@fixture(scope="package", name="default_workflow")
def fixture_default_workflow():
    yield to_asset_path("workflows", "test_default_workflow.nf")


@fixture(scope="package", name="odem_workflow")
def fixture_odem_workflow():
    yield to_asset_path("workflows", "test_odem_workflow.nf")


@fixture(scope="package", name="bytes_template_workflow")
def fixture_bytes_template_workflow(template_workflow):
    return open(template_workflow, 'rb')


@fixture(scope="package", name="bytes_default_workflow")
def fixture_bytes_default_workflow(default_workflow):
    return open(default_workflow, 'rb')


@fixture(scope="package", name="bytes_odem_workflow")
def fixture_bytes_odem_workflow(odem_workflow):
    return open(odem_workflow, 'rb')
