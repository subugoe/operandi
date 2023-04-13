from fastapi.testclient import TestClient
from pymongo import MongoClient
import pytest
import requests
import os

from operandi_server.server import OperandiServer
from ..utils_test import allocate_asset

OCRD_WEBAPI_DB_URL = os.environ["OCRD_WEBAPI_DB_URL"]
OCRD_WEBAPI_DB_NAME = os.environ["OCRD_WEBAPI_DB_NAME"]


@pytest.fixture(scope='session')
def operandi_client(start_docker_mongodb):
    operandi_app = OperandiServer(
        host="localhost",
        port=8000,
        server_url=f"http://localhost:8000",
        db_url=OCRD_WEBAPI_DB_URL,
        rmq_host="localhost",
        rmq_port=5672,
        rmq_vhost='/'
    )
    with TestClient(operandi_app) as client:
        yield client


@pytest.fixture(scope="session")
def start_docker_mongodb(docker_ip, docker_services, do_before_all_tests):
    # This returns 47017, the port configured inside tests/docker-compose.yml
    port = docker_services.port_for("mongo", 27017)
    url = f"http://{docker_ip}:{port}"

    docker_services.wait_until_responsive(
        timeout=10.0,
        pause=0.1,
        check=lambda: is_url_responsive(url, retries=10)
    )


def is_url_responsive(url, retries: int = 0):
    while True:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return True
        except Exception:
            if retries <= 0:
                return False
            retries -= 1


@pytest.fixture(scope="session", name='mongo_client')
def _fixture_mongo_client(start_docker_mongodb):
    mongo_client = MongoClient(OCRD_WEBAPI_DB_URL, serverSelectionTimeoutMS=3000)
    yield mongo_client


@pytest.fixture(scope="session", name='auth')
def _fixture_auth():
    user = os.getenv("OCRD_WEBAPI_USERNAME")
    pw = os.getenv("OCRD_WEBAPI_PASSWORD")
    yield user, pw


@pytest.fixture(scope="session", name='workspace_mongo_coll')
def _fixture_workspace_mongo_coll(mongo_client):
    mydb = mongo_client[OCRD_WEBAPI_DB_NAME]
    workspace_coll = mydb["workspace"]
    yield workspace_coll
    workspace_coll.drop()


@pytest.fixture(name='asset_workspace1')
def _fixture_asset_workspace1():
    file = {'workspace': allocate_asset("workspaces/dummy_ws.ocrd.zip")}
    yield file
