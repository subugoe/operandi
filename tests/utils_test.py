import os


def to_asset_path(name):
    path_to_module = os.path.dirname(__file__)
    return os.path.join(os.path.abspath(path_to_module), "assets", name)
