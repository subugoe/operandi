from pkg_resources import resource_filename
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
import os
import logging

__all__ = [
    "SERVER_HOST",
    "SERVER_PORT",
    "SERVER_PATH",
    "OPERANDI_DATA_PATH",
    "JOBS_DIR",
    "WORKFLOWS_DIR",
    "WORKSPACES_DIR",
    "DB_URL",
    "LOG_LEVEL",
    "LOG_FORMAT"
]

TOML_FILENAME: str = resource_filename(__name__, 'config.toml')
TOML_FD = open(TOML_FILENAME, mode='rb')
TOML_CONFIG = tomllib.load(TOML_FD)
TOML_FD.close()

SERVER_HOST: str = TOML_CONFIG["server_host"]
SERVER_PORT: int = TOML_CONFIG["server_port"]
SERVER_PATH: str = f"http://{SERVER_HOST}:{SERVER_PORT}"

# OPERANDI related data is stored inside
OPERANDI_DATA_PATH: str = TOML_CONFIG["server_data_path"]
JOBS_DIR: str = os.path.join(OPERANDI_DATA_PATH, "jobs")
WORKFLOWS_DIR: str = os.path.join(OPERANDI_DATA_PATH, "workflows")
WORKSPACES_DIR: str = os.path.join(OPERANDI_DATA_PATH, "workspaces")
DB_URL: str = TOML_CONFIG["mongodb_url"]

LOG_FORMAT: str = '%(levelname) -10s %(asctime)s %(name) -30s %(funcName) -35s %(lineno) -5d: %(message)s'
LOG_LEVEL: int = logging.INFO
