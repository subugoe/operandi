from os.path import abspath, dirname, join


def to_asset_path(resource_type, name):
    tests_module_path = dirname(__file__)
    return join(abspath(tests_module_path), "assets", resource_type, name)
