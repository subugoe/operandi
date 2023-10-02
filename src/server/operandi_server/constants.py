from dotenv import load_dotenv
from os import getenv
try:
    from tests.constants import OPERANDI_SERVER_URL_LIVE
except Exception as e:
    OPERANDI_SERVER_URL_LIVE = "http://localhost:8000"

__all__ = [
    "DEFAULT_FILE_GRP",
    "DEFAULT_METS_BASENAME",
    "SERVER_URL"
]

load_dotenv()

# TODO: Revisit this, temporal fix for the test environment
SERVER_URL: str = getenv("OPERANDI_SERVER_URL_LIVE", OPERANDI_SERVER_URL_LIVE)

DEFAULT_FILE_GRP: str = "DEFAULT"
DEFAULT_METS_BASENAME: str = "mets.xml"
