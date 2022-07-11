__all__ = [
    "SERVER_HOST",
    "SERVER_PORT",
    "SERVER_PATH",
    "PRESERVE_REQUESTS",
]

SERVER_HOST: str = "localhost"
SERVER_PORT: int = 8000
SERVER_PATH: str = f"http://{SERVER_HOST}:{SERVER_PORT}"

# Should the server safe previously accepted requests to a file?
# This may be useful in the future
PRESERVE_REQUESTS: bool = False
