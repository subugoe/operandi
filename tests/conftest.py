import os
import pytest
import shutil

OPERANDI_TESTS_DIR = os.environ['OPERANDI_TESTS_DIR']


@pytest.fixture(scope="session", autouse=True)
def do_before_all_tests():
    shutil.rmtree(OPERANDI_TESTS_DIR, ignore_errors=True)
    os.mkdir(OPERANDI_TESTS_DIR)
