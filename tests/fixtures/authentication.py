from pytest import fixture
from ..constants import (
    OCRD_WEBAPI_PASSWORD,
    OCRD_WEBAPI_USERNAME
)


@fixture(scope="session", name="auth")
def fixture_auth():
    yield OCRD_WEBAPI_USERNAME, OCRD_WEBAPI_PASSWORD
