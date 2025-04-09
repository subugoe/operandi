__all__ = [
    "DEFAULT_OPERANDI_SERVER_ROOT_URL",
    "TRIES_TILL_TIMEOUT",
    "USE_WORKSPACE_FILE_GROUP",
    "WAIT_TIME_BETWEEN_POLLS",
]

DEFAULT_OPERANDI_SERVER_ROOT_URL = "http://localhost:8000"

# Time waited between each workflow job status check
WAIT_TIME_BETWEEN_POLLS: int = 120  # seconds
# Times to perform workflow job status checks before timeout
TRIES_TILL_TIMEOUT: int = 30

USE_WORKSPACE_FILE_GROUP = "DEFAULT"
