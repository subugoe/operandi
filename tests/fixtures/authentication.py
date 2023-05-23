from pytest import fixture
from tests.constants import (
    OPERANDI_HARVESTER_DEFAULT_PASSWORD,
    OPERANDI_HARVESTER_DEFAULT_USERNAME,
    OPERANDI_SERVER_DEFAULT_PASSWORD,
    OPERANDI_SERVER_DEFAULT_USERNAME
)


@fixture(scope="session", name="auth")
def fixture_auth():
    yield OPERANDI_SERVER_DEFAULT_USERNAME, OPERANDI_SERVER_DEFAULT_PASSWORD


@fixture(scope="session", name="auth_harvester")
def fixture_auth():
    yield OPERANDI_HARVESTER_DEFAULT_USERNAME, OPERANDI_HARVESTER_DEFAULT_PASSWORD
