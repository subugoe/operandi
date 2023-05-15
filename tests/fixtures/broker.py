from pytest import fixture
from operandi_broker import ServiceBroker
from tests.constants import OCRD_RABBITMQ_URL, OCRD_WEBAPI_DB_URL


@fixture(scope="session", name="service_broker")
def fixture_operandi_broker():
    service_broker = ServiceBroker(
        db_url=OCRD_WEBAPI_DB_URL,
        rabbitmq_url=OCRD_RABBITMQ_URL
    )
    yield service_broker
    service_broker.kill_workers()
