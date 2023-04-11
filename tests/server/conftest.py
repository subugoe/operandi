import pytest
from pytest_mock import MockerFixture
from fastapi.testclient import TestClient

from operandi_server.server import OperandiServer


OPERANDI_TESTS_PATH = "/tmp/operandi_tests"


@pytest.fixture(scope='class')
def mock_init(class_mocker: MockerFixture):
    # Patch the startup function
    return class_mocker.patch('operandi_server.server.OperandiServer.startup_event')


@pytest.fixture(scope='class')
def operandi_app(class_mocker: MockerFixture):

    # Requires >= Python 3.8
    async def async_magic():
        pass

    # Async hack for MagicMock. Source:
    # https://stackoverflow.com/questions/51394411/python-object-magicmock-cant-be-used-in-await-expression
    class_mocker.MagicMock.__await__ = lambda x: async_magic().__await__()
    operandi_app = OperandiServer(
        host="localhost",
        port=8000,
        server_url=f"http://localhost:8000",
        db_url="mongodb://172.17.0.1:27018",
        rmq_host="localhost",
        rmq_port=5672,
        rmq_vhost='/'
    )
    return operandi_app


@pytest.fixture(scope='class')
def operandi_client(mock_init, operandi_app):
    with TestClient(operandi_app) as client:
        yield client
    mock_init.assert_called_once()
