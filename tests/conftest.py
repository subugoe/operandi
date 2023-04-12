import os
import pytest
import shutil

OPERANDI_TESTS_PATH = "/tmp/operandi_tests"


@pytest.fixture(scope="session", autouse=True)
def do_before_all_tests():
    shutil.rmtree(OPERANDI_TESTS_PATH, ignore_errors=True)
    os.mkdir(OPERANDI_TESTS_PATH)
