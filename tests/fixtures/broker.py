from os import environ
from pytest import fixture
from operandi_broker import ServiceBroker
from tests.helpers_asserts import assert_availability_db


@fixture(scope="session", name="service_broker")
async def fixture_operandi_broker():
    await assert_availability_db(environ.get("OPERANDI_DB_URL"))
    service_broker = ServiceBroker(test_sbatch=True)
    yield service_broker
    service_broker.kill_workers()
