from pytest import fixture


@fixture(scope="module")
def fixture_dummy():
    yield "Dummy placeholder test"
