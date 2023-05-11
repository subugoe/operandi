from pytest import fixture
from operandi_broker import ServiceBroker
from tests.constants import OCRD_WEBAPI_DB_URL


@fixture(scope="session", name="service_broker")
def fixture_operandi_broker():
    service_broker = ServiceBroker(
        db_url=OCRD_WEBAPI_DB_URL,
        rmq_host="localhost",
        rmq_port=5672,
        rmq_vhost="test",
        rmq_username="test-session",
        rmq_password="test-session"
    )
    yield service_broker
    service_broker.kill_workers()
