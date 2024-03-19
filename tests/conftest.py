from dotenv import load_dotenv
from os import environ
from pytest import fixture
from shutil import rmtree

from src.utils.operandi_utils.database import sync_db_initiate_database

pytest_plugins = [
    "tests.fixtures.authentication",
    "tests.fixtures.broker",
    "tests.fixtures.harvester",
    "tests.fixtures.hpc",
    "tests.fixtures.rabbitmq",
    "tests.fixtures.workflow",
    "tests.fixtures.workspace"
]


load_dotenv()


@fixture(scope="session", autouse=True)
def do_before_all_tests():
    rmtree(environ.get("OPERANDI_SERVER_BASE_DIR"), ignore_errors=True)
    sync_db_initiate_database(db_url=environ.get("MONGODB_URL"), db_name=environ.get("MONGODB_NAME"))
