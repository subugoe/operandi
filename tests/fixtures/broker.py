from pytest import fixture
from operandi_broker import ServiceBroker
from tests.constants import OCRD_RABBITMQ_URL, OCRD_WEBAPI_DB_URL


@fixture(scope="session", name="service_broker")
def fixture_operandi_broker():
    host, port = OCRD_RABBITMQ_URL.split(":", 1)

    service_broker = ServiceBroker(
        db_url=OCRD_WEBAPI_DB_URL,
        rmq_host=host,
        rmq_port=port,
        rmq_vhost="test",
        rmq_username="test-session",
        rmq_password="test-session"
    )
    yield service_broker
    service_broker.kill_workers()
