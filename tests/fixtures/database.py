from os import environ
from pymongo import AsyncMongoClient
from pytest import fixture, mark

from tests.helpers_asserts import assert_availability_db

DB_DROP_COLLECTIONS = ["hpc_slurm_jobs", "workflows", "workflow_jobs", "workspaces"]


@fixture(scope="session")
async def fixture_test_mongo_client():
    await assert_availability_db(environ.get("OPERANDI_DB_URL"))
    mongo_client = AsyncMongoClient(
        environ.get("OPERANDI_DB_URL"), serverSelectionTimeoutMS=3000
    )[environ.get("OPERANDI_DB_NAME")]
    # drop previous test entries from the test database
    for db_collection in DB_DROP_COLLECTIONS:
        await mongo_client[db_collection].drop()
    yield mongo_client


@fixture(scope="session", name="db_hpc_slurm_jobs")
async def fixture_db_hpc_slurm_jobs_collection(fixture_test_mongo_client):
    yield fixture_test_mongo_client["hpc_slurm_jobs"]


@fixture(scope="session", name="db_user_accounts")
async def fixture_db_user_accounts_collection(fixture_test_mongo_client):
    yield fixture_test_mongo_client["user_accounts"]


@fixture(scope="session", name="db_workflows")
async def fixture_db_workflows_collection(fixture_test_mongo_client):
    yield fixture_test_mongo_client["workflows"]


@fixture(scope="session", name="db_workflow_jobs")
async def fixture_db_workflow_jobs_collection(fixture_test_mongo_client):
    yield fixture_test_mongo_client["workflow_jobs"]


@fixture(scope="session", name="db_workspaces")
async def fixture_db_workspaces_collection(fixture_test_mongo_client):
    yield fixture_test_mongo_client["workspaces"]
