import logging

__all__ = [
    "DB_URL",
    "DEFAULT_QUEUE_SERVER_TO_BROKER",
    "LOG_FORMAT",
    "LOG_LEVEL",
    "OPERANDI_ROOT_DATA_PATH",
    "SERVER_HOST",
    "SERVER_PORT"
]

DB_URL: str = "mongodb://localhost:27018"
DEFAULT_QUEUE_SERVER_TO_BROKER: str = "operandi-server-to-broker"

LOG_FORMAT: str = '%(levelname) -7s %(asctime)s %(name) -30s %(funcName) -35s %(lineno) -5d: %(message)s'
LOG_LEVEL: int = logging.INFO

# TODO: Use this as a root data directory
OPERANDI_ROOT_DATA_PATH: str = "/tmp/operandi-data"

SERVER_HOST: str = "localhost"
SERVER_PORT: int = 8000
