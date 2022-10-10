from pkg_resources import resource_filename
import tomli
from pathlib import Path

__all__ = [
    "SERVER_HOST",
    "SERVER_PORT",
    "SERVER_PATH",
    "PRESERVE_REQUESTS",
    "OPERANDI_DATA_PATH"
]

TOML_FILENAME: str = resource_filename(__name__, 'config.toml')
TOML_FD = open(TOML_FILENAME, mode='rb')
TOML_CONFIG = tomli.load(TOML_FD)
TOML_FD.close()

SERVER_HOST: str = TOML_CONFIG["server_host"]
SERVER_PORT: int = TOML_CONFIG["server_port"]
SERVER_PATH: str = f"http://{SERVER_HOST}:{SERVER_PORT}"

# OPERANDI related data is stored inside
OPERANDI_DATA_PATH: str = f"{Path.home()}/operandi-data"

# Should the server safe previously accepted requests to a file?
# This may be useful in the future
PRESERVE_REQUESTS: bool = eval(TOML_CONFIG["preserve_requests"])
