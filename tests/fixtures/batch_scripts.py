from pytest import fixture
from tests.constants import BATCH_SCRIPT_EMPTY
from tests.helpers_utils import to_asset_path

@fixture(scope="package", name="path_batch_script_empty")
def fixture_path_batch_script_empty():
    yield to_asset_path(resource_type="batch_scripts", name=BATCH_SCRIPT_EMPTY)
