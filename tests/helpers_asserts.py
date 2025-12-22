from pytest import mark
from os.path import exists, isdir, isfile
from pymongo import AsyncMongoClient
from pymongo.errors import ServerSelectionTimeoutError


@mark.asyncio
async def assert_availability_db(db_url: str, timeout_ms: int = 5000) -> bool:
    client = AsyncMongoClient(db_url, serverSelectionTimeoutMS=timeout_ms)
    try:
        await client.admin.command("ping")
        return True
    except ServerSelectionTimeoutError:
        return False
    finally:
        await client.close()


def assert_exists_db_resource(db_resource, resource_key, resource_id):
    assert db_resource, "Resource not existing in the database"
    assert db_resource[resource_key], f"Nonexistent resource key: {resource_key}"
    assert db_resource[resource_key] == resource_id, \
        f"Wrong resource id. Expected: {resource_id}, found {db_resource[resource_key]}"


def assert_exists_db_resource_not(db_resource, resource_id):
    # Note, the resource itself is not deleted, just the flag is set
    assert db_resource, "Resource not existing in the database"
    assert db_resource["deleted"], f"DB resource entry should not exists, but does: {resource_id}"


def assert_exists_dir(dir_path: str):
    assert exists(dir_path), f"Path nonexistent: {dir_path}"
    assert isdir(dir_path), f"Path not directory: {dir_path}"


def assert_exists_file(file_path: str):
    assert exists(file_path), f"Path nonexistent: {file_path}"
    assert isfile(file_path), f"Path not file: {file_path}"


def assert_exists_not(check_path: str):
    assert not exists(check_path), f"Path should not but exists: {check_path}"
