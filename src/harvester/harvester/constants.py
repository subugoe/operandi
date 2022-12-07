from pkg_resources import resource_filename
#import tomli
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

__all__ = [
    "VD18_IDS_FILE",
    "VD18_URL",
    "VD18_METS_EXT",
    "WAIT_TIME_BETWEEN_SUBMITS",
    "POST_METHOD_TO_OPERANDI",
    "POST_METHOD_ID_PARAMETER",
    "POST_METHOD_URL_PARAMETER"
]

TOML_FILENAME: str = resource_filename(__name__, 'config.toml')
TOML_FD = open(TOML_FILENAME, mode='rb')
#TOML_CONFIG = tomli.load(TOML_FD)
TOML_CONFIG = tomllib.load(TOML_FD)
TOML_FD.close()

# These are the VD18 constants
VD18_IDS_FILE: str = resource_filename(__name__, "vd18IDs.txt")
VD18_URL: str = TOML_CONFIG["vd18_url"]
VD18_METS_EXT: str = TOML_CONFIG["vd18_mets_ext"]

# Harvesting related constants
# This is the time waited between the POST requests to the OPERANDI Server
WAIT_TIME_BETWEEN_SUBMITS: int = TOML_CONFIG["wait_time_between_submits"]  # seconds

# This is the default POST method to OPERANDI
# NOTE: Make sure that the OPERANDI Server's IP and PORT are correctly configured here!!!
POST_METHOD_TO_OPERANDI: str = TOML_CONFIG["post_method_to_operandi"]
POST_METHOD_ID_PARAMETER: str = TOML_CONFIG["post_method_id_parameter"]
POST_METHOD_URL_PARAMETER: str = TOML_CONFIG["post_method_url_parameter"]
