from pkg_resources import resource_filename
import logging

__all__ = [
    "VD18_IDS_FILE",
    "VD18_URL",
    "VD18_METS_EXT",
    "WAIT_TIME_BETWEEN_SUBMITS",
    "WAIT_TIME_BETWEEN_POLLS",
    "LOG_FORMAT",
    "LOG_LEVEL"
]

# These are the VD18 constants
# The vd18IDs.txt file contains METS IDs.
# These IDs are used to build the METS URL to be submitted to the Operandi Server.
VD18_IDS_FILE: str = resource_filename(__name__, "assets/vd18IDs.txt")
VD18_URL: str = "https://gdz.sub.uni-goettingen.de/mets/"
VD18_METS_EXT: str = ".mets.xml"

# Harvesting related constants
# This is the time waited between the POST requests to the OPERANDI Server
WAIT_TIME_BETWEEN_SUBMITS: int = 10  # seconds
# This is the time waited between checking the submitted workflow job status
WAIT_TIME_BETWEEN_POLLS: int = 10  # seconds

LOG_FORMAT: str = '%(levelname) -7s %(asctime)s %(name) -30s %(funcName) -35s %(lineno) -5d: %(message)s'
LOG_LEVEL: int = logging.INFO
