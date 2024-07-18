from pytest import fixture
from tests.helpers_utils import to_asset_path

from ..constants import BATCH_SCRIPT_EMPTY, BATCH_SCRIPTS_ROUTER_DIR, BATCH_SUBMIT_WORKFLOW_JOB


@fixture(scope="package", name="path_batch_script_empty")
def fixture_path_batch_script_empty():
    yield to_asset_path(resource_type=BATCH_SCRIPTS_ROUTER_DIR, name=BATCH_SCRIPT_EMPTY)


@fixture(scope="package", name="path_batch_script_submit_workflow_job")
def fixture_path_batch_script_submit_workflow_job():
    yield to_asset_path(resource_type=BATCH_SCRIPTS_ROUTER_DIR, name=BATCH_SUBMIT_WORKFLOW_JOB)
