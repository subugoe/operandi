from pytest import fixture
from operandi_broker import ServiceBroker
from tests.constants import OPERANDI_DB_URL, OPERANDI_RABBITMQ_URL
from tests.helpers_asserts import assert_availability_db


@fixture(scope="session", name="service_broker")
def fixture_operandi_broker():
    assert_availability_db(OPERANDI_DB_URL)
    service_broker = ServiceBroker(
        db_url=OPERANDI_DB_URL,
        rabbitmq_url=OPERANDI_RABBITMQ_URL,
        test_sbatch=True
    )
    yield service_broker
    service_broker.kill_workers()
