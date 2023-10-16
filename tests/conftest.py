from dotenv import load_dotenv
from os import environ
from pytest import fixture
from shutil import rmtree

pytest_plugins = [
    "tests.fixtures.authentication",
    "tests.fixtures.database",
    "tests.fixtures.workflow",
    "tests.fixtures.workspace"
]


load_dotenv()


@fixture(scope="session", autouse=True)
def do_before_all_tests():
    rmtree(environ.get("OPERANDI_SERVER_BASE_DIR"), ignore_errors=True)
