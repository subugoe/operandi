from os import environ

__all__ = [
    "OCRD_WEBAPI_DB_NAME",
    "OCRD_WEBAPI_DB_URL",
    "OPERANDI_TESTS_DIR"
]

OCRD_WEBAPI_DB_NAME = environ.get("OCRD_WEBAPI_DB_NAME", "test_operandi_db")
OCRD_WEBAPI_DB_URL = environ.get("OCRD_WEBAPI_DB_URL", "mongodb://localhost:27018")
OPERANDI_TESTS_DIR = environ.get("OPERANDI_TESTS_DIR", "/tmp/operandi_tests")
