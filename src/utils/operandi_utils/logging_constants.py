from dotenv import load_dotenv
from os import environ
from pathlib import Path

__all__ = [
    "OPERANDI_LOGS_DIR"
]

load_dotenv()

OPERANDI_LOGS_DIR: str = environ.get("OPERANDI_LOGS_DIR", f"/tmp/operandi_logs")
Path(OPERANDI_LOGS_DIR).mkdir(parents=True, exist_ok=True)
