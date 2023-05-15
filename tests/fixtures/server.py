from pytest import fixture
from fastapi.testclient import TestClient

from operandi_server import OperandiServer
from tests.helpers_asserts import (
    assert_availability_db,
    assert_availability_rabbitmq
)
from tests.constants import (
    OCRD_RABBITMQ_URL,
    OCRD_WEBAPI_DB_URL,
    OPERANDI_LIVE_SERVER_ADDR,
    OPERANDI_LOCAL_SERVER_ADDR
)


@fixture(scope="session", name="operandi")
def fixture_operandi_server():
    print(OCRD_RABBITMQ_URL)
    host, port = OCRD_RABBITMQ_URL.split(":", 1)

    assert_availability_db(OCRD_WEBAPI_DB_URL)
    # Checks the availability of the RabbitMQ Management UI
    assert_availability_rabbitmq(f"http://{host}:{int(port)+10000}")
    operandi_app = OperandiServer(
        local_server_url=OPERANDI_LOCAL_SERVER_ADDR,
        live_server_url=OPERANDI_LIVE_SERVER_ADDR,
        db_url=OCRD_WEBAPI_DB_URL,
        rmq_host=host,
        rmq_port=port,
        rmq_vhost="test",
        rmq_username="test-session",
        rmq_password="test-session"
    )
    with TestClient(operandi_app) as client:
        yield client
