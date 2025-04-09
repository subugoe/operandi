from pkg_resources import resource_filename

__all__ = [
    "DEFAULT_OPERANDI_SERVER_ROOT_URL",
    "TRIES_TILL_TIMEOUT",
    "USE_WORKSPACE_FILE_GROUP",
    "VD18_DATA_JSON",
    "VD18_IDS_FILE",
    "VD18_URL",
    "VD18_METS_EXT",
    "WAIT_TIME_BETWEEN_SUBMITS",
    "WAIT_TIME_BETWEEN_POLLS",
]

DEFAULT_OPERANDI_SERVER_ROOT_URL = "http://localhost:8000"

# These are the VD18 constants
# The vd18IDs.txt file contains METS IDs.
# These IDs are used to build the METS URL to be submitted to the Operandi Server.
VD18_IDS_FILE: str = resource_filename(__name__, "assets/vd18IDs.txt")
VD18_DATA_JSON: str = resource_filename(__name__, "assets/vd18_data.json")
VD18_URL: str = "https://gdz.sub.uni-goettingen.de/mets/"
VD18_METS_EXT: str = ".mets.xml"

# Time waited between the POST requests to the OPERANDI Server
WAIT_TIME_BETWEEN_SUBMITS: int = 15  # seconds
# Time waited between each workflow job status check
WAIT_TIME_BETWEEN_POLLS: int = 15  # seconds
# Times to perform workflow job status checks before timeout
TRIES_TILL_TIMEOUT: int = 30

USE_WORKSPACE_FILE_GROUP = "DEFAULT"
