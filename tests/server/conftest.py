from fastapi.testclient import TestClient
from pytest import fixture

from operandi_server.server import OperandiServer
from ..helpers_asserts import assert_availability_db
from ..helpers_utils import allocate_asset
from ..constants import OCRD_WEBAPI_DB_URL
from .constants import OCRD_WEBAPI_USERNAME, OCRD_WEBAPI_PASSWORD


@fixture(scope="session", name="operandi")
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


@fixture(scope="session", name="auth")
def fixture_auth():
    yield OCRD_WEBAPI_USERNAME, OCRD_WEBAPI_PASSWORD


@fixture(name="workflow1")
def fixture_workflow1():
    workflow_fp = allocate_asset("workflows", "nextflow_dummy.nf")
    file = {"nextflow_script": workflow_fp}
    yield file


@fixture(name="workflow2")
def fixture_workflow2():
    workflow_fp = allocate_asset("workflows", "nextflow_dummy_no_params.nf")
    file = {"nextflow_script": workflow_fp}
    yield file


@fixture(name="workspace1")
def fixture_workspace1():
    workspace_fp = allocate_asset("workspaces", "dummy_ws.ocrd.zip")
    file = {"workspace": workspace_fp}
    yield file


@fixture(name="workspace2")
def fixture_workspace2():
    workspace_fp = allocate_asset("workspaces", "example_ws_different_mets.ocrd.zip")
    file = {"workspace": workspace_fp}
    yield file
