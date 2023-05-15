from pytest import fixture
from fastapi.testclient import TestClient

from operandi_server import OperandiServer
from tests.helpers_asserts import assert_availability_db
from tests.constants import (
    OCRD_RABBITMQ_URL,
    OCRD_WEBAPI_DB_URL,
    OPERANDI_LIVE_SERVER_ADDR,
    OPERANDI_LOCAL_SERVER_ADDR
)


@fixture(scope="session", name="operandi")
def fixture_operandi_server():
    assert_availability_db(OCRD_WEBAPI_DB_URL)
    operandi_app = OperandiServer(
        local_server_url=OPERANDI_LOCAL_SERVER_ADDR,
        live_server_url=OPERANDI_LIVE_SERVER_ADDR,
        db_url=OCRD_WEBAPI_DB_URL,
        rabbitmq_url=OCRD_RABBITMQ_URL
    )
    with TestClient(operandi_app) as client:
        yield client
