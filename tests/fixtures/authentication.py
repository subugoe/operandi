from os import environ
from pytest import fixture


@fixture(scope="session", name="auth")
def fixture_auth():
    yield environ.get("OPERANDI_SERVER_DEFAULT_USERNAME"), environ.get("OPERANDI_SERVER_DEFAULT_PASSWORD")


@fixture(scope="session", name="auth_harvester")
def fixture_auth_harvester():
    yield environ.get("OPERANDI_HARVESTER_DEFAULT_USERNAME"), environ.get("OPERANDI_HARVESTER_DEFAULT_PASSWORD")
