from pymongo import MongoClient
from pytest import fixture

from tests.constants import (
    OCRD_WEBAPI_DB_NAME,
    OCRD_WEBAPI_DB_URL
)
from tests.helpers_asserts import assert_availability_db


@fixture(scope="session")
def fixture_mongo_client():
    assert_availability_db(OCRD_WEBAPI_DB_URL)
    mongo_client = MongoClient(OCRD_WEBAPI_DB_URL, serverSelectionTimeoutMS=3000)
    yield mongo_client


@fixture(scope="session", name="workspace_collection")
def fixture_mongo_workspace_collection(fixture_mongo_client):
    mydb = fixture_mongo_client[OCRD_WEBAPI_DB_NAME]
    workspace_collection = mydb["workspace"]
    yield workspace_collection
    # The collections gets dropped when the fixture is torn down
    workspace_collection.drop()


@fixture(scope="session", name="workflow_collection")
def fixture_mongo_workflow_collection(fixture_mongo_client):
    mydb = fixture_mongo_client[OCRD_WEBAPI_DB_NAME]
    workflow_collection = mydb["workflow"]
    yield workflow_collection
    # The collections gets dropped when the fixture is torn down
    workflow_collection.drop()
