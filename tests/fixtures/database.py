from pymongo import MongoClient
from pytest import fixture

from tests.constants import OPERANDI_DB_NAME, OPERANDI_DB_URL
from tests.helpers_asserts import assert_availability_db

DB_COLLECTIONS = [
    "hpc_slurm_jobs",
    "workflows",
    "workflow_jobs",
    "workspaces"
]


@fixture(scope="session")
def fixture_test_mongo_client():
    assert_availability_db(OPERANDI_DB_URL)
    mongo_client = MongoClient(OPERANDI_DB_URL, serverSelectionTimeoutMS=3000)[OPERANDI_DB_NAME]
    # drop previous test entries from the test database
    for db_collection in DB_COLLECTIONS:
        mongo_client[db_collection].drop()
    yield mongo_client


@fixture(scope="session", name="db_hpc_slurm_jobs")
def fixture_db_hpc_slurm_jobs_collection(fixture_test_mongo_client):
    yield fixture_test_mongo_client["hpc_slurm_jobs"]


@fixture(scope="session", name="db_user_accounts")
def fixture_db_user_accounts_collection(fixture_test_mongo_client):
    yield fixture_test_mongo_client["user_accounts"]


@fixture(scope="session", name="db_workflows")
def fixture_db_workflows_collection(fixture_test_mongo_client):
    yield fixture_test_mongo_client["workflows"]


@fixture(scope="session", name="db_workflow_jobs")
def fixture_db_workflow_jobs_collection(fixture_test_mongo_client):
    yield fixture_test_mongo_client["workflow_jobs"]


@fixture(scope="session", name="db_workspaces")
def fixture_db_workspaces_collection(fixture_test_mongo_client):
    yield fixture_test_mongo_client["workspaces"]
