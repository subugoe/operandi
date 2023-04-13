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
def operandi_client():
    if not (is_mongodb_responsive(OCRD_WEBAPI_DB_URL)):
        raise Exception(f"DB not running on {OCRD_WEBAPI_DB_URL}")
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


def is_mongodb_responsive(url):
    http_url = url.replace("mongodb", "http")
    response = requests.get(http_url)
    if response.status_code == 200:
        return True
    return False


@pytest.fixture(scope="session", name='mongo_client')
def _fixture_mongo_client():
    if not (is_mongodb_responsive(OCRD_WEBAPI_DB_URL)):
        raise Exception(f"DB not running on {OCRD_WEBAPI_DB_URL}")
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
    # workspace_coll.drop()


@pytest.fixture(name='asset_workspace1')
def _fixture_asset_workspace1():
    file = {'workspace': allocate_asset("workspaces/dummy_ws.ocrd.zip")}
    yield file
