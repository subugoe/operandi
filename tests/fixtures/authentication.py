from pytest import fixture
from tests.constants import (
    OPERANDI_SERVER_DEFAULT_PASSWORD,
    OPERANDI_SERVER_DEFAULT_USERNAME
)


@fixture(scope="session", name="auth")
def fixture_auth():
    yield OPERANDI_SERVER_DEFAULT_USERNAME, OPERANDI_SERVER_DEFAULT_PASSWORD
