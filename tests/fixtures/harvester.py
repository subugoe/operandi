from os import environ
from pytest import fixture
from operandi_harvester import Harvester


@fixture(scope="session", name="harvester")
def fixture_operandi_harvester(auth_harvester):
    harvester = Harvester(
        server_address=environ.get("OPERANDI_SERVER_URL_LIVE"),
        auth_username=auth_harvester[0], auth_password=auth_harvester[1])
    yield harvester
