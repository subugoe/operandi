from pathlib import Path

__all__ = [
    "SERVER_HOST",
    "SERVER_PORT",
    "SERVER_PATH",
    "PRESERVE_REQUESTS",
    "OPERANDI_DATA_PATH"
]

SERVER_HOST: str = "localhost"
SERVER_PORT: int = 8000
SERVER_PATH: str = f"http://{SERVER_HOST}:{SERVER_PORT}"

# Should the server safe previously accepted requests to a file?
# This may be useful in the future
PRESERVE_REQUESTS: bool = False

# OPERANDI related data is stored inside
OPERANDI_DATA_PATH: str = f"{Path.home()}/operandi-data"
