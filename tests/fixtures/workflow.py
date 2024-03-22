from pytest import fixture
from tests.helpers_utils import to_asset_path


@fixture(scope="package", name="template_workflow_with_ms")
def fixture_template_workflow_with_ms():
    yield to_asset_path("workflows", "test_template_workflow_with_MS.nf")


@fixture(scope="package", name="default_workflow_with_ms")
def fixture_default_workflow_with_ms():
    yield to_asset_path("workflows", "test_default_workflow_with_MS.nf")


@fixture(scope="package", name="odem_workflow_with_ms")
def fixture_odem_workflow_with_ms():
    yield to_asset_path("workflows", "test_odem_workflow_with_MS.nf")


@fixture(scope="package", name="bytes_template_workflow_with_ms")
def fixture_bytes_template_workflow_with_ms(template_workflow_with_ms):
    return open(template_workflow_with_ms, "rb")


@fixture(scope="package", name="bytes_default_workflow_with_ms")
def fixture_bytes_default_workflow_with_ms(default_workflow_with_ms):
    return open(default_workflow_with_ms, "rb")


@fixture(scope="package", name="bytes_odem_workflow_with_ms")
def fixture_bytes_odem_workflow_with_ms(odem_workflow_with_ms):
    return open(odem_workflow_with_ms, "rb")
