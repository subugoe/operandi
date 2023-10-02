from dotenv import load_dotenv
from os import environ

__all__ = [
    'DEFAULT_EXCHANGER_NAME',
    'DEFAULT_EXCHANGER_TYPE',
    'DEFAULT_QUEUE',
    'DEFAULT_QUEUE_FOR_HARVESTER',
    'DEFAULT_QUEUE_FOR_USERS',
    'DEFAULT_QUEUE_FOR_JOB_STATUSES',
    'DEFAULT_ROUTER',
    'RECONNECT_WAIT',
    'RECONNECT_TRIES',
    'PREFETCH_COUNT'
]

load_dotenv()

DEFAULT_EXCHANGER_TYPE: str = "direct"
DEFAULT_EXCHANGER_NAME: str = environ.get("OPERANDI_RABBITMQ_EXCHANGE_NAME", "operandi_default")
DEFAULT_ROUTER: str = environ.get("OPERANDI_RABBITMQ_EXCHANGE_ROUTER", "operandi_default_queue")

DEFAULT_QUEUE: str = environ.get("OPERANDI_RABBITMQ_QUEUE_DEFAULT", "operandi_default_queue")
DEFAULT_QUEUE_FOR_HARVESTER: str = environ.get("OPERANDI_RABBITMQ_QUEUE_HARVESTER", "operandi_queue_harvester")
DEFAULT_QUEUE_FOR_USERS: str = environ.get("OPERANDI_RABBITMQ_QUEUE_USERS", "operandi_queue_users")
DEFAULT_QUEUE_FOR_JOB_STATUSES: str = environ.get("OPERANDI_RABBITMQ_QUEUE_JOB_STATUSES", "operandi_queue_job_statuses")

# Wait seconds before next reconnect try
RECONNECT_WAIT: int = 5
# Reconnect tries before timeout
RECONNECT_TRIES: int = 3
# QOS, i.e., how many messages to consume in a single go
# Check here: https://www.rabbitmq.com/consumer-prefetch.html
PREFETCH_COUNT: int = 1
