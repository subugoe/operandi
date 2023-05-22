from dotenv import load_dotenv
from os import environ
from pathlib import Path

try:
    from importlib.metadata import distribution as get_distribution
except ImportError:
    from importlib_metadata import distribution as get_distribution

__all__ = [
    "OPERANDI_LOGS_DIR",
    "OPERANDI_VERSION"
]

load_dotenv()

OPERANDI_VERSION = get_distribution('operandi_utils').version
OPERANDI_LOGS_DIR: str = environ.get("OPERANDI_LOGS_DIR", "/tmp/operandi_logs")
Path(OPERANDI_LOGS_DIR).mkdir(parents=True, exist_ok=True)
