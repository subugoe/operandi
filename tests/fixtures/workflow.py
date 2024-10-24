from pytest import fixture
from tests.constants import WORKFLOWS_ROUTER_DIR
from tests.helpers_utils import to_asset_path


@fixture(scope="package", name="template_workflow")
def fixture_template_workflow():
    yield to_asset_path(resource_type=WORKFLOWS_ROUTER_DIR, name="test_template_workflow.nf")

@fixture(scope="package", name="default_workflow")
def fixture_default_workflow():
    yield to_asset_path(resource_type=WORKFLOWS_ROUTER_DIR, name="test_default_workflow.nf")

@fixture(scope="package", name="odem_workflow")
def fixture_odem_workflow():
    yield to_asset_path(resource_type=WORKFLOWS_ROUTER_DIR, name="test_odem_workflow.nf")

@fixture(scope="package", name="sbb_workflow")
def fixture_sbb_workflow():
    yield to_asset_path(resource_type=WORKFLOWS_ROUTER_DIR, name="test_sbb_workflow.nf")


@fixture(scope="package", name="template_workflow_with_ms")
def fixture_template_workflow_with_ms():
    yield to_asset_path(resource_type=WORKFLOWS_ROUTER_DIR, name="test_template_workflow_with_MS.nf")

@fixture(scope="package", name="default_workflow_with_ms")
def fixture_default_workflow_with_ms():
    yield to_asset_path(resource_type=WORKFLOWS_ROUTER_DIR, name="test_default_workflow_with_MS.nf")

@fixture(scope="package", name="odem_workflow_with_ms")
def fixture_odem_workflow_with_ms():
    yield to_asset_path(resource_type=WORKFLOWS_ROUTER_DIR, name="test_odem_workflow_with_MS.nf")

@fixture(scope="package", name="sbb_workflow_with_ms")
def fixture_sbb_workflow_with_ms():
    yield to_asset_path(resource_type=WORKFLOWS_ROUTER_DIR, name="test_sbb_workflow_with_MS.nf")


@fixture(scope="package", name="bytes_template_workflow")
def fixture_bytes_template_workflow(template_workflow):
    return open(file=template_workflow, mode="rb")

@fixture(scope="package", name="bytes_default_workflow")
def fixture_bytes_default_workflow(default_workflow):
    return open(file=default_workflow, mode="rb")

@fixture(scope="package", name="bytes_odem_workflow")
def fixture_bytes_odem_workflow(odem_workflow):
    return open(file=odem_workflow, mode="rb")

@fixture(scope="package", name="bytes_sbb_workflow")
def fixture_bytes_sbb_workflow(sbb_workflow):
    return open(file=sbb_workflow, mode="rb")


@fixture(scope="package", name="bytes_template_workflow_with_ms")
def fixture_bytes_template_workflow_with_ms(template_workflow_with_ms):
    return open(file=template_workflow_with_ms, mode="rb")

@fixture(scope="package", name="bytes_default_workflow_with_ms")
def fixture_bytes_default_workflow_with_ms(default_workflow_with_ms):
    return open(file=default_workflow_with_ms, mode="rb")

@fixture(scope="package", name="bytes_odem_workflow_with_ms")
def fixture_bytes_odem_workflow_with_ms(odem_workflow_with_ms):
    return open(file=odem_workflow_with_ms, mode="rb")

@fixture(scope="package", name="bytes_sbb_workflow_with_ms")
def fixture_bytes_sbb_workflow_with_ms(sbb_workflow_with_ms):
    return open(file=sbb_workflow_with_ms, mode="rb")
