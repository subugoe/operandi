from fastapi.testclient import TestClient
from os import environ
from pytest import fixture
from operandi_server import OperandiServer
from tests.helpers_asserts import assert_availability_db


@fixture(scope="package", name="operandi")
def fixture_operandi_server():
    assert_availability_db(environ.get("OPERANDI_DB_URL"))
    operandi_app = OperandiServer()
    with TestClient(operandi_app) as client:
        yield client

"""
from httpx import ASGITransport, AsyncClient
@fixture(scope="package", name="operandi")
async def fixture_operandi_server():
    await assert_availability_db(environ.get("OPERANDI_DB_URL"))
    async with AsyncClient(
        transport=ASGITransport(app=OperandiServer()),
        base_url="http://testserver"
    ) as client:
        yield client
"""
