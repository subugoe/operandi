from pkg_resources import resource_filename
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
import logging

__all__ = [
    "VD18_IDS_FILE",
    "VD18_URL",
    "VD18_METS_EXT",
    "WAIT_TIME_BETWEEN_SUBMITS",
    "LOG_FORMAT",
    "LOG_LEVEL"
]

TOML_FILENAME: str = resource_filename(__name__, 'config.toml')
TOML_FD = open(TOML_FILENAME, mode='rb')
TOML_CONFIG = tomllib.load(TOML_FD)
TOML_FD.close()

# These are the VD18 constants
VD18_IDS_FILE: str = resource_filename(__name__, "vd18IDs.txt")
VD18_URL: str = TOML_CONFIG["vd18_url"]
VD18_METS_EXT: str = TOML_CONFIG["vd18_mets_ext"]

# Harvesting related constants
# This is the time waited between the POST requests to the OPERANDI Server
WAIT_TIME_BETWEEN_SUBMITS: int = TOML_CONFIG["wait_time_between_submits"]  # seconds

LOG_FORMAT: str = '%(levelname) -10s %(asctime)s %(name) -30s %(funcName) -35s %(lineno) -5d: %(message)s'
LOG_LEVEL: int = logging.INFO
