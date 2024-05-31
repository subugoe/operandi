from pytest import fixture
from tests.helpers_utils import to_asset_path

BATCH_SCRIPTS_ROUTER_DIR = "batch_scripts"


@fixture(scope="package", name="path_batch_script_empty")
def fixture_path_batch_script_empty():
    yield to_asset_path(resource_type=BATCH_SCRIPTS_ROUTER_DIR, name="test_empty.sh")


@fixture(scope="package", name="path_batch_script_submit_workflow_job")
def fixture_path_batch_script_submit_workflow_job():
    yield to_asset_path(resource_type=BATCH_SCRIPTS_ROUTER_DIR, name="submit_workflow_job.sh")
