from pytest import fixture
from fastapi.testclient import TestClient

from operandi_server import OperandiServer
from tests.helpers_asserts import assert_availability_db
from tests.constants import (
    OPERANDI_RABBITMQ_URL,
    OPERANDI_DB_URL,
    OPERANDI_SERVER_URL_LIVE,
    OPERANDI_SERVER_URL_LOCAL
)


@fixture(scope="session", name="operandi")
def fixture_operandi_server():
    assert_availability_db(OPERANDI_DB_URL)
    operandi_app = OperandiServer(
        local_server_url=OPERANDI_SERVER_URL_LOCAL,
        live_server_url=OPERANDI_SERVER_URL_LIVE,
        db_url=OPERANDI_DB_URL,
        rabbitmq_url=OPERANDI_RABBITMQ_URL
    )
    with TestClient(operandi_app) as client:
        yield client
