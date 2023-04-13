from fastapi.testclient import TestClient
from pytest import fixture

from operandi_server.server import OperandiServer
from ..helpers_asserts import assert_availability_db
from ..helpers_utils import to_asset_path
from ..constants import OCRD_WEBAPI_DB_URL
from .constants import OCRD_WEBAPI_USERNAME, OCRD_WEBAPI_PASSWORD


@fixture(scope="module", name="operandi")
def fixture_operandi_server():
    assert_availability_db(OCRD_WEBAPI_DB_URL)
    operandi_app = OperandiServer(
        host="localhost",
        port=48000,
        server_url=f"http://localhost:48000",
        db_url=OCRD_WEBAPI_DB_URL,
        rmq_host="localhost",
        rmq_port=5672,
        rmq_vhost="/"
    )
    with TestClient(operandi_app) as client:
        yield client


@fixture(scope="module", name="auth")
def fixture_auth():
    yield OCRD_WEBAPI_USERNAME, OCRD_WEBAPI_PASSWORD


@fixture(scope="module")
def fixture_workspace1():
    workspace_fp = open(to_asset_path("workspaces", "dummy_ws.ocrd.zip"), "rb")
    file = {"workspace": workspace_fp}
    yield file
