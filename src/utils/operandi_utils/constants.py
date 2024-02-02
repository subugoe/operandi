from dotenv import load_dotenv

try:
    from importlib.metadata import distribution as get_distribution
except ImportError:
    from importlib_metadata import distribution as get_distribution

__all__ = [
    "LOG_FORMAT",
    "LOG_LEVEL_BROKER",
    "LOG_LEVEL_HARVESTER",
    "LOG_LEVEL_RMQ_CONSUMER",
    "LOG_LEVEL_RMQ_PUBLISHER",
    "LOG_LEVEL_SERVER",
    "LOG_LEVEL_WORKER",
    "MODULE_TYPES",
    "OLA_HD_BAG_ENDPOINT",
    "OLA_HD_USER",
    "OLA_HD_PASSWORD",
    "OPERANDI_VERSION"
]

load_dotenv()

LOG_FORMAT: str = "%(levelname) -7s %(asctime)s %(name) -30s %(funcName) -35s %(lineno) -5d: %(message)s"
LOG_LEVEL_SERVER: str = "INFO"
LOG_LEVEL_HARVESTER: str = "INFO"
LOG_LEVEL_BROKER: str = "INFO"
LOG_LEVEL_WORKER: str = "INFO"
LOG_LEVEL_RMQ_CONSUMER: str = "INFO"
LOG_LEVEL_RMQ_PUBLISHER: str = "INFO"

MODULE_TYPES = ["server", "harvester", "broker", "worker"]

# Notes left by @joschrew
# OLA-HD development instance, reachable only when connected to GÖNET
OLA_HD_BAG_ENDPOINT = "http://141.5.99.53/api/bag"
# The credentials are already publicly available inside the OLA-HD repo
# Ignore docker warnings about exposed credentials
OLA_HD_USER = "admin"
OLA_HD_PASSWORD = "JW24G.xR"

OPERANDI_VERSION = get_distribution("operandi_utils").version
